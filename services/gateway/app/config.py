from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_", env_file=".env", extra="ignore")

    service_name: str = "llm-inference-gateway"
    environment: str = "local"
    backend_kind: str = Field(default="mock", pattern="^(mock|openai_compatible|ollama)$")
    backend_url: str = "http://127.0.0.1:11434"
    backend_timeout_seconds: float = 30.0
    max_prompt_chars: int = 16_000
    default_model: str = "llama3.2"
    otlp_endpoint: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Load and cache application settings from environment variables."""
    return Settings()
