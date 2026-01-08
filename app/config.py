from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # App
    app_name: str = "Requirement Gathering Agent"
    debug: bool = True
    BASE_DIR: Path = BASE_DIR

    # Redis
    redis_host: str
    redis_port: int
    redis_db: int
    redis_ttl_seconds: int | None = None

    @field_validator("redis_ttl_seconds", mode="before")
    @classmethod
    def parse_none_string(cls, v):
        if isinstance(v, str) and v.lower() == "none":
            return None
        return v

    # JWT Auth
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # OpenRouter
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-oss-120b:free"
    openrouter_fallback_model: str = "xiaomi/mimo-v2-flash:free"

    # LangSmith Monitoring
    langchain_tracing_v2: str = "false"
    langchain_api_key: str | None = None
    langchain_project: str = "Default Project"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # Export
    EXPORT_XLSX_DIR: Path = BASE_DIR / "exports_xlsx"
    PROMPTS_JSON_DIR: Path = BASE_DIR / "exports_prompts_json"
    EXPORT_JSON_DIR: Path = BASE_DIR / "exports_json"
    EXPORT_BRANDING_DIR: Path = BASE_DIR / "exports_branding_xlsx"
    EXPORT_ESTIMATED_DIR: Path = BASE_DIR / "estimated_pages_json"
    EXPORT_PROMPTS_DIR: Path = BASE_DIR / "exports_prompts_json"
    EXPORT_IMAGES_DIR: Path = BASE_DIR / "exports_branding_images"

    postgres_user: str
    postgres_password: str
    postgres_server: str
    postgres_port: int
    postgres_db: str

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
