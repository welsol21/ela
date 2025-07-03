# ========== core/pipeline.py ==========
"""
Core processing pipeline:
 - Initialize or migrate cache database
 - Transcribe audio -> sentences
 - Translate sentences
 - Generate TTS clips
 - Generate output artifacts
 - Cache via SQLite
"""
import os
import json
from typing import List, Dict, Any

# Import database utilities
from core.db_utils import init_cache_db, CACHE_DB

# Initialize cache at module load (ensures DB created)
init_cache_db(CACHE_DB)


def transcribe(audio_path: str) -> List[Dict[str, Any]]:
    """Transcribe audio and return list of sentence dicts with text, start, end timestamps."""
    # TODO: implement using OpenAI Whisper + SpaCy
    # Placeholder:
    return []


def translate(sentences: List[Dict[str, Any]], service: str) -> List[Dict[str, Any]]:
    """Translate each sentence using the chosen service (OpenAI, DeepL, etc.)."""
    # TODO: implement translation logic
    return sentences


def generate_tts(translated_sentences: List[Dict[str, Any]], voice: str, cache_dir: str) -> List[str]:
    """Generate TTS audio clips using edge-tts, return paths to audio files."""
    # TODO: implement TTS generation
    return []


def generate_outputs(
    original_sentences: List[Dict[str, Any]],
    translated_sentences: List[Dict[str, Any]],
    tts_paths: List[str],
    output_dir: str,
    suffix: str
) -> None:
    """Mix audio, write subtitles (SRT), create video (MP4), transcript (TXT), and JSON report."""
    # TODO: implement artifact generation (pydub, pysubs2, ffmpeg)
    report_path = os.path.join(output_dir, f"bilingual_objects_{suffix}.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(translated_sentences, f, ensure_ascii=False, indent=2)


def process_file(
    input_path: str,
    output_dir: str,
    translator: str,
    voice: str,
    subtitle_mode: int,
    cache_db: str = CACHE_DB
) -> None:
    """Run the full pipeline: transcription, translation, TTS, outputs."""
    # Ensure cache DB is initialized
    init_cache_db(cache_db)

    # 1. Transcription
    sentences = transcribe(input_path)

    # 2. Translation
    translated = translate(sentences, service=translator)

    # 3. TTS
    tts_clips = generate_tts(translated, voice=voice, cache_dir=cache_db)

    # 4. Artifact generation
    generate_outputs(sentences, translated, tts_clips, output_dir, suffix="mvp1")


# End of core/pipeline.py