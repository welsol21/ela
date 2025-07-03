# ========== core/pipeline.py ==========
"""
Core processing pipeline:
 - transcribe(audio_path) -> List[Sentence]
 - translate(sentences, service) -> List[TranslatedSentence]
 - generate_tts(translated_sentences, voice) -> List[TTSClip]
 - generate_outputs(sentences, tts_clips, output_dir, suffix)
 - caching via SQLite
"""
from typing import List, Dict, Any
import os, json


def transcribe(audio_path: str) -> List[Dict[str, Any]]:
    # 1. Возвращаем одну «фиктивную» фразу
    return [{"id": 1, "text": "Hello world.", "start": 0.0, "end": 1.0}]


def translate(sentences: List[Dict[str, Any]], service: str) -> List[Dict[str, Any]]:
    # 2. Дублируем оригинальный текст как «перевод»
    for s in sentences:
        s["text_translated"] = s["text"]
    return sentences


def generate_tts(translated_sentences: List[Dict[str, Any]], voice: str, cache_dir: str) -> List[str]:
    # 3. Пропускаем синтез речи
    return []


def generate_outputs(original_sentences: List[Dict[str, Any]],
                     translated_sentences: List[Dict[str, Any]],
                     tts_paths: List[str],
                     output_dir: str,
                     suffix: str) -> None:
    # 4. Записываем итоговый JSON
    out_path = os.path.join(output_dir, f"bilingual_objects_{suffix}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(translated_sentences, f, ensure_ascii=False, indent=2)


def process_file(input_path: str,
                 output_dir: str,
                 translator: str,
                 voice: str,
                 subtitle_mode: int,
                 cache_db: str) -> None:
    sentences = transcribe(input_path)
    translated = translate(sentences, service=translator)
    tts_clips = generate_tts(translated, voice, cache_dir=cache_db)
    generate_outputs(sentences, translated, tts_clips, output_dir, suffix="mvp1")
