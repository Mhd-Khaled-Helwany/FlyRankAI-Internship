from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = PROJECT_ROOT / "prompts"

@lru_cache(maxsize=None)
def load_prompt(filename: str) -> str:
    """Read a prompt file's raw text, cached after the first read.
    """
    path = PROMPTS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Prompt file not found: {path}. Expected it under {PROMPTS_DIR}."
        )
    return path.read_text(encoding="utf-8").strip()
 
def get_enrich_system_prompt() -> str:
    return load_prompt("enrich-v1.md")