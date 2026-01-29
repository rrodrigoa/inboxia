from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/inboxia"
    redis_url: str = "redis://redis:6379/0"
    provider: str = "stub"
    openai_api_key: str | None = None
    frontend_backend_url: str = "http://localhost:8000"


settings = Settings()
