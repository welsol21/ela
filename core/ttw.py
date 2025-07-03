# ========== core/tta.py ==========
"""
Main pipeline logic for English Language Assistant. Based on transcribe_and_translate_windows.py.
Uses SQLite database (cache.db) for caching transcripts and translations.
"""

import os
import json
import time
import re
import asyncio
import shutil
import tempfile
import hashlib
import subprocess

import whisper
import spacy
import edge_tts
import deepl
import pysubs2
from pysubs2 import Alignment
from pydub import AudioSegment
from PIL import Image
from tqdm import tqdm
from transformers import pipeline
from openai import OpenAI, OpenAIError
from lara_sdk import Credentials, Translator as LaraTranslator, LaraApiError
import sqlite3

def run_pipeline_main(audio_path, translator_choice, voice_choice, subtitle_mode, tmpdir, db_config, output_dir):
    start_time = time.time()
    _suffix_map = {
        "gpt": "gpt",
        "deepl": "deepl",
        "lara": "lara",
        "hf": "hf",
        "original": "en"
    }
    suffix = _suffix_map.get(translator_choice.lower(), "hf")

    # Load binary content to compute hashes
    with open(audio_path, "rb") as f:
        data = f.read()
    data_hash = hashlib.sha256(data).hexdigest()

    vc = voice_choice if voice_choice is not None else ""
    full_hash = hashlib.sha256(
        data + translator_choice.encode() + subtitle_mode.encode() + vc.encode()
    ).hexdigest()

    # Connect to SQLite
    db_path = db_config["database"]
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Helpers for cache access
    def select_semantic_units(cursor, data_hash):
        cursor.execute("SELECT semantic_units FROM file_cache WHERE data_hash = ?", (data_hash,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def insert_semantic_units(cursor, data_hash, units_json):
        cursor.execute("INSERT INTO file_cache (data_hash, semantic_units) VALUES (?, ?)", (data_hash, units_json))

    def select_bilingual_objects(cursor, full_hash):
        cursor.execute("SELECT bilingual_objects FROM translation_cache WHERE full_hash = ?", (full_hash,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def insert_bilingual_objects(cursor, full_hash, data_hash, bo_json):
        cursor.execute(
            "INSERT INTO translation_cache (full_hash, data_hash, bilingual_objects) VALUES (?, ?, ?)",
            (full_hash, data_hash, bo_json)
        )

    # Check for transcript
    units = select_semantic_units(cur, data_hash)
    if units is not None:
        skip_transcribe = True
        print("Transcript found in file_cache, skipping transcription.")
    else:
        skip_transcribe = False

    # Download model if needed
    try:
        spacy.load("en_core_web_sm")
    except OSError:
        print("Downloading spaCy model en_core_web_sm...")
        from spacy.cli import download
        download("en_core_web_sm")

    if not skip_transcribe:
        model = whisper.load_model("medium")
        nlp_en = spacy.load("en_core_web_sm")
        if "sentencizer" not in nlp_en.pipe_names:
            nlp_en.add_pipe("sentencizer")

        print("Transcribing audio...")
        result = model.transcribe(audio_path, language="en", word_timestamps=True, verbose=True)

        def build_semantic_units(transcription):
            ulist, uid = [], 1
            for seg in transcription["segments"]:
                for w in seg["words"]:
                    raw = w["word"].strip()
                    if not raw:
                        continue
                    for tok in re.findall(r"\d+|[A-Za-z]+|[^\w\s]", raw):
                        utype = "number" if tok.isdigit() else ("word" if tok.isalpha() else "symbol")
                        ulist.append({
                            "id": uid,
                            "type": utype,
                            "text": tok,
                            "audio": {
                                "origin_start": w["start"],
                                "origin_end": w["end"]
                            }
                        })
                        uid += 1
            return ulist

        units = build_semantic_units(result)
        su_json = json.dumps(units, ensure_ascii=False)
        insert_semantic_units(cur, data_hash, su_json)
        conn.commit()
        print("✅ Transcription saved to file_cache.")

    def group_units_by_sentence(units_list):
        sentences_list = []
        buffer = []
        sid = 1
        for u in units_list:
            buffer.append(u)
            if u["type"] == "symbol" and u["text"] in ".?!":
                text = "".join(
                    (t["text"] if t["type"] == "symbol" else " " + t["text"])
                    for t in buffer
                ).strip()
                sentences_list.append({
                    "id": sid,
                    "text_eng": text,
                    "units": buffer.copy(),
                    "start": buffer[0]["audio"]["origin_start"],
                    "end": buffer[-1]["audio"]["origin_end"]
                })
                sid += 1
                buffer.clear()
        if buffer:
            text = " ".join(t["text"] for t in buffer).strip()
            sentences_list.append({
                "id": sid,
                "text_eng": text,
                "units": buffer.copy(),
                "start": buffer[0]["audio"]["origin_start"],
                "end": buffer[-1]["audio"]["origin_end"]
            })
        return sentences_list

    sentences = group_units_by_sentence(units)

    bilingual_objects = select_bilingual_objects(cur, full_hash)
    skip_translate = (bilingual_objects is not None)
    if skip_translate:
        sentences = bilingual_objects
        print("Translation found in translation_cache, skipping translation.")
    gpt_client = None
    deepl_translator = None
    lara_translator = None
    hf_translator = None

    if translator_choice == "g":
        gpt_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif translator_choice == "d":
        deepl_translator = deepl.Translator(os.getenv("DEEPL_AUTH_KEY"))
    elif translator_choice == "l":
        lara_creds = Credentials(
            access_key_id=os.getenv("LARA_API_ID"),
            access_key_secret=os.getenv("LARA_API_SECRET")
        )
        lara_translator = LaraTranslator(lara_creds)
    elif translator_choice == "h":
        hf_translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-ru")

    voice = None
    if translator_choice != "n" and subtitle_mode in ("1", "2", "4"):
        voice = "ru-RU-SvetlanaNeural" if voice_choice == "f" else "ru-RU-DmitryNeural"

    async def _tts_save(text: str, voice: str, path: str) -> bool:
        try:
            await edge_tts.Communicate(text, voice).save(path)
            return os.path.exists(path) and os.path.getsize(path) > 1024
        except:
            return False

    def try_generate_tts(text: str, voice: str, path: str, retries: int = 3) -> bool:
        for i in range(1, retries + 1):
            if asyncio.run(_tts_save(text, voice, path)):
                return True
            time.sleep(1)
        return False

    def translate(text: str) -> str:
        if translator_choice == "g":
            resp = gpt_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Переведи литературно на русский: {text}"}],
                temperature=0.3
            )
            return resp.choices[0].message.content.strip()
        elif translator_choice == "d":
            return deepl_translator.translate_text(text, target_lang="RU").text
        elif translator_choice == "l":
            res = lara_translator.translate(text, source="en-US", target="ru-RU")
            return res.translation
        elif translator_choice == "h":
            return hf_translator(text, max_length=512)[0]["translation_text"]
        elif translator_choice == "n":
            return ""
        else:
            raise RuntimeError("Unsupported translation mode.")

    def enrich_with_translation(sentences: list, tmpdir: str):
        for s in tqdm(sentences, desc="Translating & synthesizing"):
            if subtitle_mode == "0":
                s["text_ru"] = ""
                s["audio_ru_path"] = None
                s["units_ru"] = []
                continue

            if re.fullmatch(r"[.?!\s]+", s["text_eng"]):
                s["text_ru"] = s["text_eng"]
                path = os.path.join(tmpdir, f"ru_{s['id']}.mp3")
                AudioSegment.silent(duration=100).export(path, format="mp3")
                s["audio_ru_path"], s["units_ru"] = path, []
                continue

            ru = translate(s["text_eng"])
            s["text_ru"] = ru
            path = os.path.join(tmpdir, f"ru_{s['id']}.mp3")

            if subtitle_mode in ("1", "2", "4"):
                if try_generate_tts(ru, voice, path):
                    dur = len(AudioSegment.from_file(path))
                    s["audio_ru_path"] = path
                else:
                    s["audio_ru_path"] = None
                    dur = 0
            else:
                s["audio_ru_path"] = None
                dur = 0

            toks = re.findall(r"\d+|[A-Za-zА-Яа-яЁё]+|[^\w\s]", ru)
            off, ru_units = 0, []
            avg = (dur or 0) / max(len(toks), 1)
            for uid2, tok in enumerate(toks, start=1):
                ttype = "number" if tok.isdigit() else ("word" if tok.isalpha() else "symbol")
                ru_units.append({
                    "id": uid2,
                    "type": ttype,
                    "text": tok,
                    "audio": {
                        "origin_start": off / 1000,
                        "origin_end": (off + avg) / 1000
                    }
                })
                off += avg
            s["units_ru"] = ru_units

    if not skip_translate:
        enrich_with_translation(sentences, tmpdir)
        bo_json = json.dumps(sentences, ensure_ascii=False)
        insert_bilingual_objects(cur, full_hash, data_hash, bo_json)
        conn.commit()
        print("✅ Translation and TTS saved to translation_cache.")
    else:
        enrich_with_translation(sentences, tmpdir)
    
    def generate_outputs(sentences: list, audio_path: str, tmpdir: str, suffix: str, output_dir: str) -> None:
        full = AudioSegment.from_file(audio_path)
        out = AudioSegment.empty()

        subs = pysubs2.SSAFile()
        subs.styles["Top"] = pysubs2.SSAStyle(
            fontname="Arial", fontsize=22, bold=True,
            alignment=Alignment.TOP_CENTER
        )
        subs.styles["Bottom"] = pysubs2.SSAStyle(
            fontname="Arial", fontsize=22, bold=True,
            alignment=Alignment.BOTTOM_CENTER
        )

        base = os.path.splitext(os.path.basename(audio_path))[0]
        base_path = os.path.join(output_dir, base)

        with open(f"{base_path}_semantic_units_{suffix}.json", "w", encoding="utf-8") as f:
            json.dump(sentences, f, ensure_ascii=False, indent=2)
        with open(f"{base_path}_bilingual_objects_{suffix}.json", "w", encoding="utf-8") as f:
            json.dump(sentences, f, ensure_ascii=False, indent=2)

        for idx, s in enumerate(tqdm(sentences, desc="Building A/V"), start=1):
            st, et = int(s["start"] * 1000), int(s["end"] * 1000)
            eng = full[st:et].fade_in(1).fade_out(1)
            dur_e = len(eng)
            pos_en = len(out)
            out += eng

            if subtitle_mode in ("0", "1"):
                subs.append(pysubs2.SSAEvent(
                    start=pos_en,
                    end=pos_en + dur_e,
                    text=s["text_eng"],
                    style="Top"
                ))

            if subtitle_mode in ("1", "2", "3", "4"):
                out += AudioSegment.silent(duration=10)

                if subtitle_mode == "1":
                    pos_ru = len(out)
                    if s["audio_ru_path"]:
                        ru_audio = AudioSegment.from_file(s["audio_ru_path"]).fade_in(3)
                        out += ru_audio
                        dur_r = len(ru_audio)
                    else:
                        dur_r = 0
                    subs.append(pysubs2.SSAEvent(
                        start=pos_ru,
                        end=pos_ru + dur_r,
                        text=s["text_ru"],
                        style="Top"
                    ))

                elif subtitle_mode == "4":
                    if s["audio_ru_path"]:
                        ru_audio = AudioSegment.from_file(s["audio_ru_path"]).fade_in(3)
                    else:
                        ru_audio = AudioSegment.silent(0)
                    pos_ru = len(out)
                    out += ru_audio
                    end_ru = len(out)
                    subs.append(pysubs2.SSAEvent(
                        start=pos_en,
                        end=end_ru,
                        text=s["text_ru"],
                        style="Top"
                    ))

                elif subtitle_mode == "2":
                    out += AudioSegment.silent(duration=10)
                    pos_ru = len(out)
                    if s["audio_ru_path"]:
                        ru_audio = AudioSegment.from_file(s["audio_ru_path"]).fade_in(3)
                        out += ru_audio
                        dur_r = len(ru_audio)
                    else:
                        dur_r = 0
                    end_all = pos_ru + dur_r
                    subs.append(pysubs2.SSAEvent(
                        start=pos_en,
                        end=end_all,
                        text=s["text_eng"],
                        style="Top"
                    ))
                    subs.append(pysubs2.SSAEvent(
                        start=pos_en,
                        end=end_all,
                        text=s["text_ru"],
                        style="Bottom"
                    ))

                elif subtitle_mode == "3":
                    subs.append(pysubs2.SSAEvent(
                        start=pos_en,
                        end=pos_en + dur_e,
                        text=s["text_ru"],
                        style="Top"
                    ))

            if idx < len(sentences):
                gap = int((sentences[idx]["start"] - s["end"]) * 1000)
                out += AudioSegment.silent(duration=max(gap // 3, 10))

        mp3_out = f"{base_path}_bilingual_{suffix}.mp3"
        srt_out = f"{base_path}_bilingual_{suffix}.srt"
        mp4_out = f"{base_path}_bilingual_{suffix}.mp4"
        txt_out = f"{base_path}_bilingual_{suffix}.txt"
        ass_path = os.path.join(tmpdir, "subs.ass")

        subs.save(ass_path)
        subs.save(srt_out)
        print("Exporting MP3…")
        out.export(mp3_out, format="mp3")

        black = os.path.join(tmpdir, "black.jpg")
        Image.new("RGB", (1280, 720), color="black").save(black)
        safe_ass = ass_path.replace('\\', '\\\\').replace(':', '\\:')
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-framerate", "2",
            "-i", black, "-i", mp3_out,
            "-vf", f"ass='{safe_ass}'",
            "-c:v", "libx264", "-tune", "stillimage", "-shortest",
            "-c:a", "aac", "-b:a", "192k", "-map", "0:v", "-map", "1:a",
            mp4_out
        ]
        print("Generating video (ffmpeg)…")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("Saving JSON and .txt…")
        with open(txt_out, "w", encoding="utf-8") as f:
            json.dump(sentences, f, ensure_ascii=False, indent=2)

        print("✅ Done:")
        print(" •", mp3_out)
        print(" •", mp4_out)
        print(" •", srt_out)
        print(" •", txt_out)

    generate_outputs(sentences, audio_path, tmpdir, suffix, output_dir)

    shutil.rmtree(tmpdir)
    cur.close()
    conn.close()

    elapsed = time.time() - start_time
    print(f"Execution time: {elapsed:.2f} sec.")
