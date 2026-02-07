from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    db_dir = Path.home() / ".audio-mastering-tool"
    return f"sqlite+aiosqlite:///{db_dir / 'audio_mastering.db'}"


class Settings(BaseSettings):
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


settings = Settings()
