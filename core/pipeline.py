# ========== core/pipeline.py ==========
"""
Wrapper to run main pipeline logic from ttw.py with arguments provided by UI or CLI.
"""

# ========== core/pipeline.py ==========
"""
Wrapper to run main pipeline logic from ttw.py with arguments provided by UI or CLI.
"""

import tempfile
import os
from core.ttw import run_pipeline_main
from core.db_utils import CACHE_DB

def process_file(audio_path, output_dir, translator_code, voice_choice, subtitle_mode, ui_callback=None):
    import tempfile
    import core.ttw as tta

    with tempfile.TemporaryDirectory() as tmpdir:
        db_config = {"database": "cache.db"}
        tta.run_pipeline_main(
            audio_path=audio_path,
            translator_choice=translator_code,
            voice_choice=voice_choice,
            subtitle_mode=str(subtitle_mode),
            tmpdir=tmpdir,
            db_config=db_config,
            output_dir=output_dir,
            ui_callback=ui_callback  # <- добавлено
        )
