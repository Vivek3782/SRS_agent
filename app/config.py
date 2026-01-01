from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Requirement Gathering Agent"
    debug: bool = True

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_ttl_seconds: int = 3600


settings = Settings()
