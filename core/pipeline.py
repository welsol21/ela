# ========== core/pipeline.py ==========

"""
Wrapper to run main pipeline logic from ttw.py with arguments provided by UI or CLI.
"""

import tempfile
from core.ttw import run_pipeline_main
from core.db_utils import CACHE_DB

def process_file(
    audio_path: str,
    output_dir: str,
    translator_choice: str,
    voice_choice: str,
    subtitle_mode: int
) -> None:
    run_pipeline_main(
        audio_path=audio_path,
        translator_choice=translator_choice,
        voice_choice=voice_choice,
        subtitle_mode=str(subtitle_mode),
        tmpdir=tempfile.mkdtemp(),
        db_config={"database": CACHE_DB},
        output_dir=output_dir
    )
