"""Tests for provider abstraction: interface parity, streaming, switching, failure handling."""
import pytest

from app.providers import get_provider
from app.providers.groq_provider import GroqProvider
from app.providers.ollama_provider import OllamaProvider


def test_provider_switching_returns_correct_class():
    assert isinstance(get_provider("ollama"), OllamaProvider)
    assert isinstance(get_provider("groq"), GroqProvider)


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_provider("not-a-provider")


@pytest.mark.asyncio
async def test_ollama_streaming(monkeypatch):
    provider = OllamaProvider()

    class FakeStream:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def raise_for_status(self):
            pass

        async def aiter_lines(self):
            import json
            yield json.dumps({"message": {"content": "Hello"}, "done": False})
            yield json.dumps({"message": {"content": " world"}, "done": True})

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def stream(self, *a, **kw):
            return FakeStream()

    monkeypatch.setattr("app.providers.ollama_provider.httpx.AsyncClient", lambda **kw: FakeClient())

    chunks = [c async for c in provider.generate_response(messages=[{"role": "user", "content": "hi"}], system_prompt="sys")]
    assert "".join(chunks) == "Hello world"


@pytest.mark.asyncio
async def test_groq_missing_api_key_handled(monkeypatch):
    provider = GroqProvider()
    provider.api_key = ""
    chunks = [c async for c in provider.generate_response(messages=[{"role": "user", "content": "hi"}], system_prompt="sys")]
    assert "GROQ_API_KEY" in "".join(chunks)


@pytest.mark.asyncio
async def test_ollama_health_check_failure(monkeypatch):
    provider = OllamaProvider()

    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **kw):
            import httpx
            raise httpx.ConnectError("refused")

    monkeypatch.setattr("app.providers.ollama_provider.httpx.AsyncClient", lambda **kw: FailingClient())
    assert await provider.health_check() is False
