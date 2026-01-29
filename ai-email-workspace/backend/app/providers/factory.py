from app.core.config import settings
from app.providers.base import LLMProvider
from app.providers.openai import OpenAIProvider
from app.providers.stub import LocalStubProvider


def get_provider() -> LLMProvider:
    if settings.provider == "openai":
        return OpenAIProvider()
    return LocalStubProvider()
