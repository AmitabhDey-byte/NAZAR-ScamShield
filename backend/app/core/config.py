from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NAZAR API"
    database_url: str = "sqlite+aiosqlite:///./nazar.db"
    database_url_unpooled: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_timeout_seconds: float = 12.0
    n8n_webhook_secret: str | None = None
    public_api_url: str | None = None
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    allowed_origin_regex: str | None = r"^https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.vercel\.app$"
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def database_label(self) -> str:
        return "lakebase-postgres" if "postgres" in self.database_url else "local-sqlite"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
