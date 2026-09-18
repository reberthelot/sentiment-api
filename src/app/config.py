import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Environment-driven configuration dataclass for the sentiment API."""

    project_root: Path = Path(__file__).resolve().parent.parent.parent
    wordlist_file: Path = Path(
        os.getenv(
            "WORDLIST_FILE",
            str(Path(__file__).resolve().parent.parent.parent / "word_sentiment.csv"),
        )
    )
    static_dir: Path = Path(
        os.getenv(
            "STATIC_DIR",
            str(Path(__file__).resolve().parent.parent.parent / "frontend" / "static"),
        )
    )
    templates_dir: Path = Path(
        os.getenv(
            "TEMPLATES_DIR",
            str(Path(__file__).resolve().parent.parent.parent / "frontend" / "templates"),
        )
    )
    default_service_url: str = os.getenv("DEFAULT_SERVICE_URL", "http://localhost:8000")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "4.0"))


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
