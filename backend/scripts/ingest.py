"""
Transcript ingestion pipeline.

Expected file format in agent_transcripts/*.md (or .txt):

    ---
    episode_title: How Superhuman Builds Product
    guest_name: Rahul Vohra
    publication_date: 2023-05-01
    ---
    [00:00] Intro text...
    [05:30] Talking about PMF...
    ...

Each `[HH:MM]` marker becomes the timestamp_ref for chunks starting near it.
Chunking: ~500-800 tokens (approximated via words) with ~100-token overlap.
Idempotent: a chunk_hash (sha256 of episode_title+chunk_text) enforces uniqueness,
so re-running ingestion skips already-inserted chunks.
"""
import asyncio
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import AsyncSessionLocal, init_db
from app.models.db_models import TranscriptChunk
from app.rag.embeddings import embed_batch

TRANSCRIPTS_DIR = Path(__file__).resolve().parents[2] / "agent_transcripts"
CHUNK_WORDS = 650  # approx 500-800 tokens
OVERLAP_WORDS = 90  # approx 100-token overlap

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
TIMESTAMP_RE = re.compile(r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw_meta, body = match.groups()
    meta = {}
    for line in raw_meta.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


def chunk_body(body: str) -> list[dict]:
    """Split body into overlapping word-based chunks, tracking the nearest preceding timestamp."""
    words = body.split()
    # map word index -> nearest timestamp seen so far
    timestamps_at_pos = []
    running_ts = None
    for m in TIMESTAMP_RE.finditer(body):
        char_pos = m.start()
        word_pos = len(body[:char_pos].split())
        running_ts = m.group(1)
        timestamps_at_pos.append((word_pos, running_ts))

    def ts_for_word(idx: int) -> str | None:
        ts = None
        for pos, val in timestamps_at_pos:
            if pos <= idx:
                ts = val
            else:
                break
        return ts

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_WORDS, len(words))
        chunk_words = words[start:end]
        text = " ".join(chunk_words)
        text = TIMESTAMP_RE.sub("", text).strip()
        if text:
            chunks.append({"text": text, "timestamp_ref": ts_for_word(start)})
        if end == len(words):
            break
        start = end - OVERLAP_WORDS
    return chunks


def chunk_hash(episode_title: str, text: str) -> str:
    return hashlib.sha256(f"{episode_title}::{text}".encode("utf-8")).hexdigest()


async def ingest_file(path: Path, session) -> int:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    episode_title = meta.get("episode_title", path.stem)
    guest_name = meta.get("guest_name", "Unknown Guest")
    publication_date = meta.get("publication_date")

    chunks = chunk_body(body)
    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = embed_batch(texts)

    inserted = 0
    for c, emb in zip(chunks, embeddings):
        h = chunk_hash(episode_title, c["text"])
        existing = await session.execute(select(TranscriptChunk.id).where(TranscriptChunk.chunk_hash == h))
        if existing.scalar_one_or_none():
            continue
        session.add(
            TranscriptChunk(
                episode_title=episode_title,
                guest_name=guest_name,
                publication_date=publication_date,
                timestamp_ref=c["timestamp_ref"],
                chunk_text=c["text"],
                chunk_hash=h,
                embedding=emb,
                meta={"source_file": path.name},
            )
        )
        inserted += 1
    await session.commit()
    return inserted


async def main():
    await init_db()
    files = sorted(list(TRANSCRIPTS_DIR.glob("*.md")) + list(TRANSCRIPTS_DIR.glob("*.txt")))
    if not files:
        print(f"No transcript files found in {TRANSCRIPTS_DIR}")
        return

    total = 0
    async with AsyncSessionLocal() as session:
        for path in files:
            n = await ingest_file(path, session)
            print(f"{path.name}: inserted {n} new chunk(s)")
            total += n
    print(f"Done. Total new chunks inserted: {total}")


if __name__ == "__main__":
    asyncio.run(main())
