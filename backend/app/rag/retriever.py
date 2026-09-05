"""Reusable transcript retriever: query -> embedding -> pgvector cosine search -> filtered, ranked chunks."""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.db_models import TranscriptChunk
from app.rag.embeddings import embed_text


@dataclass
class RetrievedChunk:
    episode_title: str
    guest_name: str
    timestamp_ref: str | None
    chunk_text: str
    similarity: float


class TranscriptRetriever:
    """Encapsulates all RAG retrieval logic, independent of FastAPI route handlers."""

    def __init__(self, top_k: int = None, similarity_threshold: float = None):
        self.top_k = top_k or settings.top_k
        self.similarity_threshold = (
            similarity_threshold if similarity_threshold is not None else settings.similarity_threshold
        )

    async def retrieve(self, db: AsyncSession, query: str) -> list[RetrievedChunk]:
        query_embedding = embed_text(query)

        # cosine_distance = 1 - cosine_similarity for normalized vectors in pgvector
        distance = TranscriptChunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(TranscriptChunk, distance.label("distance"))
            .order_by(distance)
            .limit(self.top_k)
        )
        result = await db.execute(stmt)
        rows = result.all()

        chunks: list[RetrievedChunk] = []
        for chunk, dist in rows:
            similarity = 1.0 - float(dist)
            if similarity < self.similarity_threshold:
                continue
            chunks.append(
                RetrievedChunk(
                    episode_title=chunk.episode_title,
                    guest_name=chunk.guest_name,
                    timestamp_ref=chunk.timestamp_ref,
                    chunk_text=chunk.chunk_text,
                    similarity=round(similarity, 4),
                )
            )
        chunks.sort(key=lambda c: c.similarity, reverse=True)
        return chunks

    @staticmethod
    def build_context(chunks: list[RetrievedChunk]) -> str:
        parts = []
        for c in chunks:
            citation = f"[Episode: {c.guest_name}, {c.timestamp_ref or c.episode_title}]"
            parts.append(f"{citation}\n{c.chunk_text}")
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def has_sufficient_context(chunks: list[RetrievedChunk]) -> bool:
        return len(chunks) > 0
