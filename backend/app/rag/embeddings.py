"""Embedding generation using sentence-transformers (all-MiniLM-L6-v2, 384-dim).

The sentence-transformers import is deliberately lazy (inside get_embedder) so that
modules importing this file for retrieval logic/tests don't pay the torch import cost
or require the model to be downloaded unless embeddings are actually generated.
"""
from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def get_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def embed_text(text: str) -> list[float]:
    model = get_embedder()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    vecs = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return vecs.tolist()
