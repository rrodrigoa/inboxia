from abc import ABC, abstractmethod
from typing import List


class LLMProvider(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    @abstractmethod
    def chat(self, prompt: str) -> str:
        raise NotImplementedError
