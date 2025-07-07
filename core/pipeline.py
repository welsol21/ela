# ========== core/pipeline.py ==========
"""
Wrapper to run the main pipeline logic from ttw.py with arguments provided by UI or CLI.
"""
import os
import tempfile
from core import ttw

def process_file(audio_path, output_dir, translator_code, voice_choice, subtitle_mode, ui_callback=None):
    # Use a temporary directory for intermediate files during processing
    with tempfile.TemporaryDirectory() as tmpdir:
        db_config = {"database": "cache.db"}
        ttw.run_pipeline_main(
            audio_path=audio_path,
            translator_choice=translator_code,
            voice_choice=voice_choice,
            subtitle_mode=str(subtitle_mode),
            tmpdir=tmpdir,
            db_config=db_config,
            output_dir=output_dir,
            ui_callback=ui_callback
        )
