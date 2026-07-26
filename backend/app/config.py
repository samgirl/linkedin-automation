from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "PROS"
    app_env: str = "development"
    secret_key: str = "change-me"
    frontend_url: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://pros:pros@localhost:5432/pros"

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_async_driver(cls, v: str) -> str:
        if not v:
            return v
        # Normalize postgres:// to postgresql:// (common with Neon, Heroku)
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Strip all SSL params from URL — asyncpg handles SSL via connect_args in database.py
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        parsed = urlparse(v)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for key in ("sslmode", "ssl"):
            qs.pop(key, None)
        new_query = urlencode(qs, doseq=True) if qs else ""
        v = urlunparse(parsed._replace(query=new_query))
        return v
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/api/auth/callback/linkedin"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback/google"

    default_ai_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # ChromaDB — optional. If not set, falls back to PostgreSQL text search.
    chroma_host: str = ""
    chroma_port: int = 8000

    encryption_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
