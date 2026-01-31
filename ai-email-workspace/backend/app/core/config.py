from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/inboxia"
    redis_url: str = "redis://redis:6379/0"
    provider: str = "stub"
    llm_provider: str | None = None
    chat_model: str | None = None
    embedding_model: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    frontend_backend_url: str = "http://localhost:8000"


settings = Settings()
