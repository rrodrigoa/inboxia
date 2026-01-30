from app.core.config import settings
from app.providers.base import LLMProvider
from app.providers.openai import OpenAIProvider
from app.providers.stub import LocalStubProvider


def get_provider() -> LLMProvider:
    provider_name = (settings.llm_provider or settings.provider).lower()
    if provider_name in {"openai", "openai_compatible"}:
        return OpenAIProvider()
    return LocalStubProvider()
