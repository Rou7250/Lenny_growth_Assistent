"""Common async streaming interface every LLM provider must implement."""
from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate_response(
        self,
        messages: list[dict],
        system_prompt: str,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """Yield response text chunks (tokens) as they are generated."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
