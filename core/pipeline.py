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

def process_file(
    audio_path: str,
    translator_code: str,
    voice_choice: str,
    subtitle_mode: int,
    output_dir: str
) -> None:
    run_pipeline_main(
        audio_path=audio_path,
        translator_choice=translator_code,
        voice_choice=voice_choice,
        subtitle_mode=str(subtitle_mode),
        tmpdir=tempfile.mkdtemp(),
        output_dir=output_dir,
        db_config={"engine": "sqlite", "database": CACHE_DB}
    )
