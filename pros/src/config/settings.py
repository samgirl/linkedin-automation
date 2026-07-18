"""Application configuration."""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "src" / "ai" / "prompts"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
PROMPTS_DIR.mkdir(exist_ok=True)


class AIConfig(BaseSettings):
    """AI provider configuration."""
    
    provider: str = Field(default="ollama", description="AI provider: ollama, openai, openrouter")
    
    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.1:8b")
    
    # OpenAI
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o")
    
    # OpenRouter
    openrouter_api_key: str = Field(default="")
    openrouter_model: str = Field(default="openai/gpt-4o")
    
    # Embeddings
    embedding_model: str = Field(default="nomic-embed-text")
    embedding_dimensions: int = Field(default=768)
    
    # Generation
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1000)

    model_config = {"env_prefix": "AI_"}


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    url: str = Field(default=f"sqlite+aiosqlite:///{DATA_DIR / 'pros.db'}")
    echo: bool = Field(default=False)

    model_config = {"env_prefix": "DB_"}


class RedisConfig(BaseSettings):
    """Redis configuration."""
    
    url: str = Field(default="redis://localhost:6379")
    db: int = Field(default=0)

    model_config = {"env_prefix": "REDIS_"}


class ChromaConfig(BaseSettings):
    """ChromaDB configuration."""
    
    host: str = Field(default="localhost")
    port: int = Field(default=8000)

    model_config = {"env_prefix": "CHROMA_"}


class ScannerConfig(BaseSettings):
    """Scanner configuration."""
    
    scan_interval_hours: int = Field(default=4)
    max_results_per_scan: int = Field(default=50)
    linkedin_enabled: bool = Field(default=True)
    github_enabled: bool = Field(default=True)
    rss_enabled: bool = Field(default=True)

    model_config = {"env_prefix": "SCANNER_"}


class Settings(BaseSettings):
    """Main application settings."""
    
    app_name: str = "PROS"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False)
    host: str = Field(default="localhost")
    port: int = Field(default=8000)
    
    # Sub-configs
    ai: AIConfig = Field(default_factory=AIConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)

    model_config = {"env_prefix": "PROS_"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
