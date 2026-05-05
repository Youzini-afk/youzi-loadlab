from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "YouziLoadLab"
    app_env: str = Field(default="development", alias="APP_ENV")
    app_secret_key: str = Field(default="dev-secret-key-dev-secret-key-32", alias="APP_SECRET_KEY")
    admin_password: str = Field(default="dev-admin-password", alias="ADMIN_PASSWORD")
    database_url: str = Field(default="sqlite:///./youziloadlab.dev.db", alias="DATABASE_URL")
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    runner_workdir: str = Field(default="./data/runs", alias="RUNNER_WORKDIR")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:8000",
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
