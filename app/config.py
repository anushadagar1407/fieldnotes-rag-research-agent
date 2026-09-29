from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default=PROJECT_DIR / "data", validation_alias="DATA_DIR")
    uploads_dir: Path = Field(
        default=PROJECT_DIR / "data" / "uploads", validation_alias="UPLOADS_DIR"
    )
    index_path: Path = Field(
        default=PROJECT_DIR / "data" / "index.json", validation_alias="INDEX_PATH"
    )
    log_path: Path = Field(
        default=PROJECT_DIR / "data" / "query_log.jsonl", validation_alias="LOG_PATH"
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-latest", validation_alias="ANTHROPIC_MODEL"
    )
    top_k: int = Field(default=5, ge=1, validation_alias="TOP_K")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")


settings = Settings()
