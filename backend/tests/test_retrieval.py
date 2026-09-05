"""Tests for TranscriptRetriever: relevance, similarity threshold, empty retrieval handling."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.retriever import TranscriptRetriever, RetrievedChunk


@pytest.mark.asyncio
async def test_relevant_chunks_pass_threshold(monkeypatch):
    retriever = TranscriptRetriever(top_k=5, similarity_threshold=0.65)

    fake_chunk = MagicMock(episode_title="Ep1", guest_name="Guest A", timestamp_ref="10:00", chunk_text="Retention tip")
    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(fake_chunk, 0.2)]  # distance 0.2 -> similarity 0.8
    db.execute.return_value = result

    monkeypatch.setattr("app.rag.retriever.embed_text", lambda q: [0.0] * 384)

    chunks = await retriever.retrieve(db, "how do I improve retention?")
    assert len(chunks) == 1
    assert chunks[0].similarity == 0.8


@pytest.mark.asyncio
async def test_similarity_threshold_filters_low_matches(monkeypatch):
    retriever = TranscriptRetriever(top_k=5, similarity_threshold=0.65)

    fake_chunk = MagicMock(episode_title="Ep1", guest_name="Guest A", timestamp_ref="10:00", chunk_text="Unrelated")
    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(fake_chunk, 0.6)]  # similarity 0.4 -> below threshold
    db.execute.return_value = result

    monkeypatch.setattr("app.rag.retriever.embed_text", lambda q: [0.0] * 384)

    chunks = await retriever.retrieve(db, "unrelated question")
    assert chunks == []


@pytest.mark.asyncio
async def test_empty_retrieval_handled(monkeypatch):
    retriever = TranscriptRetriever()
    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = []
    db.execute.return_value = result

    monkeypatch.setattr("app.rag.retriever.embed_text", lambda q: [0.0] * 384)

    chunks = await retriever.retrieve(db, "anything")
    assert chunks == []
    assert retriever.has_sufficient_context(chunks) is False
