from typing import List

import httpx

from app.core.config import settings
from app.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        provider_name = (settings.llm_provider or settings.provider).lower()
        if not settings.openai_api_key and provider_name != "openai_compatible":
            raise ValueError("OPENAI_API_KEY is required for OpenAIProvider")
        self.api_key = settings.openai_api_key or ""
        self.base_url = settings.openai_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    def _raise_for_unreachable(self, exc: Exception) -> None:
        raise RuntimeError(
            f"LLM service at {self.base_url} is unreachable or misconfigured. "
            "Verify the service is running and OPENAI_BASE_URL is correct."
        ) from exc

    def embed(self, texts: List[str]) -> List[List[float]]:
        payload = {"model": settings.openai_embedding_model, "input": texts}
        try:
            response = httpx.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            self._raise_for_unreachable(exc)
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    def chat(self, prompt: str) -> str:
        payload = {
            "model": settings.openai_chat_model,
            "messages": [
                {"role": "system", "content": "You are an assistant for an email workspace. Follow instructions."},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            self._raise_for_unreachable(exc)
        data = response.json()
        return data["choices"][0]["message"]["content"]
