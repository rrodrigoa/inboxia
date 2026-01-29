import hashlib
from typing import List

from app.providers.base import LLMProvider


class LocalStubProvider(LLMProvider):
    def embed(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            values = [b / 255.0 for b in digest]
            vector = (values * (1536 // len(values) + 1))[:1536]
            vectors.append(vector)
        return vectors

    def chat(self, prompt: str) -> str:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]
        return (
            "Stub response: This is a deterministic answer based on the prompt hash "
            f"{digest}. Please replace with a real provider in production."
        )
