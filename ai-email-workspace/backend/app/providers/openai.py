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

    def _resolve_chat_model(self) -> str:
        if not settings.openai_chat_model:
            raise RuntimeError(
                "Chat model is not configured. Set OPENAI_CHAT_MODEL to the model "
                "name served by your OpenAI-compatible endpoint."
            )
        return settings.chat_model or settings.openai_chat_model

    def _resolve_embedding_model(self) -> str:
        if not settings.openai_embedding_model:
            raise RuntimeError(
                "Embedding model is not configured. Set OPENAI_EMBEDDING_MODEL to "
                "a model that supports /v1/embeddings."
            )
        return settings.embedding_model or settings.openai_embedding_model

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
        embedding_model = self._resolve_embedding_model()
        chat_model = self._resolve_chat_model()
        if embedding_model == chat_model:
            raise RuntimeError(
                "Embedding model matches the chat model. Configure OPENAI_EMBEDDING_MODEL "
                "to a model that supports /v1/embeddings."
            )
        payload = {"model": embedding_model, "input": texts}
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
        if "data" in data and isinstance(data["data"], list):
            embeddings: List[List[float]] = []
            for item in data["data"]:
                if "embedding" not in item:
                    raise RuntimeError(
                        "Embedding response is missing an embedding field. "
                        f"Received: {data}"
                    )
                embeddings.append(item["embedding"])
            return embeddings
        if "embedding" in data:
            return [data["embedding"]]
        if "embeddings" in data:
            return data["embeddings"]
        if "error" in data:
            error = data["error"]
            message = ""
            if isinstance(error, dict):
                message = str(error.get("message", ""))
            elif isinstance(error, str):
                message = error
            if "does not support" in message and "Embedding" in message:
                raise RuntimeError(
                    "Embedding request failed because the selected model does not "
                    "support the Embeddings API. Configure OPENAI_EMBEDDING_MODEL "
                    "to a model that supports /v1/embeddings (or switch providers). "
                    f"Original error: {error}"
                )
            raise RuntimeError(f"Embedding request failed: {error}")
        raise RuntimeError(f"Unexpected embedding response from {self.base_url}: {data}")

    def chat(self, prompt: str) -> str:
        payload = {
            "model": self._resolve_chat_model(),
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
