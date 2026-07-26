import os
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from functools import lru_cache


def _detect_backend_url() -> str:
    """Detect the backend's own public URL from common hosting env vars."""
    for var in ("RENDER_EXTERNAL_URL", "RAILWAY_PUBLIC_DOMAIN", "HEROKU_APP_NAME"):
        val = os.environ.get(var, "")
        if val:
            if not val.startswith("http"):
                val = f"https://{val}"
            return val.rstrip("/")
    return "http://localhost:8000"


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
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
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
    linkedin_redirect_uri: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    default_ai_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    chroma_host: str = ""
    chroma_port: int = 8000

    encryption_key: str = ""

    @model_validator(mode="after")
    def _auto_derive_urls(self):
        backend = _detect_backend_url()

        if not self.linkedin_redirect_uri:
            self.linkedin_redirect_uri = f"{backend}/api/auth/callback/linkedin"
        if not self.google_redirect_uri:
            self.google_redirect_uri = f"{backend}/api/auth/callback/google"

        if self.frontend_url == "http://localhost:5173" and self.app_env == "production":
            self.frontend_url = "https://pros-frontend-eight.vercel.app"

        return self

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
