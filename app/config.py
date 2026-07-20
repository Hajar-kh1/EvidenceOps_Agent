from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    model_provider: Literal["openai"] = "openai"
    openai_api_key: str | None = Field(default=None, repr=False)
    llm_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    data_dir: Path = Path("data")
    storage_dir: Path = Path("storage")
    reports_dir: Path = Path("reports")
    top_k: int = Field(default=10, ge=1, le=20)
    chunk_size: int = Field(default=700, ge=200, le=2000)
    chunk_overlap: int = Field(default=100, ge=0, le=500)
    max_tool_calls: int = Field(default=8, ge=1, le=30)

    @model_validator(mode="after")
    def validate_chunking(self) -> "AppConfig":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self

    def require_model_credentials(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing from .env")


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
