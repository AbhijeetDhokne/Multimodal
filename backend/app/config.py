from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables / backend/.env."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "ConstructIQ API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    ai_provider: Literal["auto", "gemini", "openai", "demo"] = "auto"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    ai_timeout_seconds: float = 60.0
    ai_max_output_tokens: int = 3000

    max_upload_mb: int = 8
    max_image_edge_px: int = 1280

    weather_provider: Literal["auto", "offline"] = "auto"
    weather_timeout_seconds: float = 12.0
    weather_cache_seconds: int = 600

    @field_validator("cors_origins")
    @classmethod
    def _strip_origins(cls, value: str) -> str:
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def resolved_provider(self) -> str:
        """Resolve the AI provider that will actually be used."""
        if self.ai_provider == "gemini":
            return "gemini" if self.gemini_api_key.strip() else "demo"
        if self.ai_provider == "openai":
            return "openai" if self.openai_api_key.strip() else "demo"
        if self.ai_provider == "demo":
            return "demo"
        if self.gemini_api_key.strip():
            return "gemini"
        if self.openai_api_key.strip():
            return "openai"
        return "demo"

    @property
    def resolved_model(self) -> str | None:
        provider = self.resolved_provider
        if provider == "gemini":
            return self.gemini_model
        if provider == "openai":
            return self.openai_model
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
