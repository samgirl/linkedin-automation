"""Application configuration management."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

load_dotenv(BASE_DIR / ".env")


class AIConfig(BaseModel):
    provider: str = Field(default_factory=lambda: os.getenv("AI_PROVIDER", "gemini"))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    openrouter_api_key: str = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    openrouter_model: str = Field(default_factory=lambda: os.getenv("OPENROUTER_MODEL", "openai/gpt-4o"))
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3"))
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    embedding_model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    temperature: float = Field(default_factory=lambda: float(os.getenv("AI_TEMPERATURE", "0.7")))
    max_tokens: int = Field(default_factory=lambda: int(os.getenv("AI_MAX_TOKENS", "500")))
    max_comment_words: int = Field(default_factory=lambda: int(os.getenv("MAX_COMMENT_WORDS", "120")))

    @property
    def active_model(self) -> str:
        if self.provider == "openai":
            return self.openai_model
        elif self.provider == "openrouter":
            return self.openrouter_model
        elif self.provider == "ollama":
            return self.ollama_model
        elif self.provider == "gemini":
            return self.gemini_model
        return self.gemini_model

    @property
    def api_key(self) -> str:
        if self.provider == "openai":
            return self.openai_api_key
        elif self.provider == "openrouter":
            return self.openrouter_api_key
        elif self.provider == "gemini":
            return self.gemini_api_key
        return ""


class SearchConfig(BaseModel):
    max_results: int = Field(default_factory=lambda: int(os.getenv("MAX_RESULTS_PER_SEARCH", "200")))
    min_ranking_score: int = Field(default_factory=lambda: int(os.getenv("MIN_RANKING_SCORE", "40")))


class CacheConfig(BaseModel):
    ttl_hours: int = Field(default_factory=lambda: int(os.getenv("CACHE_TTL_HOURS", "24")))


class LogConfig(BaseModel):
    level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    file: str = Field(default_factory=lambda: str(DATA_DIR / "content_radar.log"))


class AppConfig(BaseModel):
    ai: AIConfig = AIConfig()
    search: SearchConfig = SearchConfig()
    cache: CacheConfig = CacheConfig()
    log: LogConfig = LogConfig()
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", f"sqlite:///{DATA_DIR / 'content_radar.db'}"
        )
    )

    def ensure_dirs(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        PROMPTS_DIR.mkdir(parents=True, exist_ok=True)


config = AppConfig()
config.ensure_dirs()
