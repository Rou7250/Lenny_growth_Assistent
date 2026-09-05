import json
from typing import AsyncIterator

import httpx

from app.config import settings
from app.providers.base import BaseLLMProvider

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(BaseLLMProvider):
    name = "groq"

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model

    async def generate_response(
        self, messages: list[dict], system_prompt: str, temperature: float = 0.3
    ) -> AsyncIterator[str]:
        if not self.api_key:
            yield "[Groq provider error: GROQ_API_KEY is not configured]"
            return

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "temperature": temperature,
            "stream": True,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", GROQ_URL, json=payload, headers=headers) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[len("data: "):]
                        if data_str.strip() == "[DONE]":
                            break
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
        except httpx.HTTPError as exc:
            yield f"\n[Groq provider error: {exc}]"

    async def health_check(self) -> bool:
        return bool(self.api_key)
