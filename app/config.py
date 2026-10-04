from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    """Load a tiny .env subset without adding a dependency."""
    dotenv_path = Path(".env")
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    app_name: str = "Study Planner Agent API"
    app_env: str = "development"
    log_level: str = "INFO"
    log_file: str | None = None


def get_settings() -> Settings:
    _load_dotenv()
    log_file = os.getenv("LOG_FILE", "").strip() or None
    return Settings(
        app_name=os.getenv("APP_NAME", Settings.app_name),
        app_env=os.getenv("APP_ENV", Settings.app_env),
        log_level=os.getenv("LOG_LEVEL", Settings.log_level).upper(),
        log_file=log_file,
    )

