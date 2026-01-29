from typing import List

import httpx

from app.core.config import settings
from app.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIProvider")
        self.api_key = settings.openai_api_key

    def embed(self, texts: List[str]) -> List[List[float]]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": "text-embedding-3-small", "input": texts}
        response = httpx.post("https://api.openai.com/v1/embeddings", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    def chat(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are an assistant for an email workspace. Follow instructions."},
                {"role": "user", "content": prompt},
            ],
        }
        response = httpx.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
