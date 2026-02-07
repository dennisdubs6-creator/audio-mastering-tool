"""
Application settings loaded from environment variables / ``.env`` file.
"""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    """Return the default synchronous SQLite URL under the user home directory."""
    db_dir = Path.home() / ".audio-mastering-tool"
    return f"sqlite:///{db_dir / 'audio_mastering.db'}"


def _default_log_file() -> str:
    """Return the default log file path under the user home directory."""
    return str(Path.home() / ".audio-mastering-tool" / "logs" / "backend.log")


class Settings(BaseSettings):
    """Application-wide settings.

    Values are read from environment variables or ``.env`` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: str = _default_database_url()
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    DEBUG: bool = False
    REFERENCE_TRACK_PATH: str = "./data/reference_tracks"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = _default_log_file()

    @model_validator(mode="after")
    def _expand_sqlite_path(self) -> "Settings":
        """Expand ``~`` in DATABASE_URL so SQLite uses the real home directory."""
        prefix = "sqlite:///"
        if self.DATABASE_URL.startswith(prefix):
            raw_path = self.DATABASE_URL[len(prefix):]
            expanded = str(Path(raw_path).expanduser())
            self.DATABASE_URL = prefix + expanded
        return self


settings = Settings()
