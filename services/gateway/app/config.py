from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_", env_file=".env", extra="ignore")

    service_name: str = "llm-inference-gateway"
    environment: str = "local"
    backend_kind: str = Field(default="mock", pattern="^(mock|openai_compatible)$")
    backend_url: str = "http://llm-backend:8000"
    backend_timeout_seconds: float = 30.0
    max_prompt_chars: int = 16_000
    default_model: str = "resume-llm"
    otlp_endpoint: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
