# Architecture

## System architecture
```
React + Vite (frontend)
      | HTTP / SSE
      v
FastAPI (backend)
      |
      +--------------------+
      |                    |
      v                    v
PostgreSQL + pgvector   LLM Router
      |                    |
      |              +-----+------+
      |              |            |
      v              v            v
Transcript RAG    Ollama        Groq
```
The frontend never talks to the database or LLM providers directly — all access is mediated
by FastAPI, which keeps the Groq API key server-side only.

## RAG pipeline
1. User submits a question via `POST /api/chat`.
2. FastAPI embeds the query with `all-MiniLM-L6-v2` (384-dim, normalized).
3. `TranscriptRetriever` runs a pgvector cosine-distance search (`<=>` operator via SQLAlchemy's
   `cosine_distance`) against `transcript_chunks`, ordered ascending by distance, limited to `TOP_K` (default 5).
4. Each result's similarity (`1 - distance`) is compared against `SIMILARITY_THRESHOLD` (default 0.65); chunks below threshold are discarded.
5. If zero chunks remain, the API short-circuits and streams back the fixed
   "I do not have sufficient information..." response — no LLM call is made, so it's impossible
   to hallucinate an answer in this path.
6. Otherwise, surviving chunks are sorted by similarity descending and concatenated into a
   context block, each prefixed with its `[Episode: Guest Name, Timestamp/Topic]` citation.

## Database schema
- `transcript_chunks(id, episode_title, guest_name, publication_date, timestamp_ref, chunk_text, chunk_hash UNIQUE, embedding VECTOR(384), meta JSONB, created_at)`
  - `chunk_hash` (sha256 of episode_title+chunk_text) enforces ingestion idempotency.
  - An HNSW index (`vector_cosine_ops`) is created on `embedding` at startup for fast ANN search.
- `sessions(id, title, created_at, updated_at)`
- `messages(id, session_id FK, role, content, sources JSONB, created_at)`
- `artifacts(id, message_id FK, artifact_type, content, title, created_at)`

## Embedding pipeline
`app/rag/embeddings.py` lazily loads a singleton `SentenceTransformer("all-MiniLM-L6-v2")`
(import deferred to avoid paying the torch/model cost for code paths that don't need it, e.g.
tests). `embed_text` / `embed_batch` both L2-normalize output so pgvector cosine distance behaves
as expected.

Ingestion (`backend/scripts/ingest.py`):
- Parses YAML-ish frontmatter (`episode_title`, `guest_name`, `publication_date`) plus a body
  containing `[HH:MM]` timestamp markers.
- Chunks the body into ~650-word (≈500–800 token) windows with a 90-word (≈100-token) overlap.
- Tracks the nearest preceding timestamp for each chunk as its `timestamp_ref`.
- Computes a stable `chunk_hash` and skips insertion if that hash already exists — safe to re-run.

## LLM provider abstraction
`app/providers/base.py` defines `BaseLLMProvider` with two async methods:
`generate_response(messages, system_prompt, temperature) -> AsyncIterator[str]` and
`health_check() -> bool`. `OllamaProvider` and `GroqProvider` both implement this interface by
streaming from their respective chat-completions endpoints. `app/providers/__init__.get_provider(name)`
is the single factory function the rest of the app depends on — routes and RAG logic never
import a concrete provider class directly, so adding a third provider requires no changes
outside `app/providers/`.

## Ollama/Groq routing
The `provider` field on `POST /api/chat` (`"ollama"` | `"groq"`) selects which concrete provider
`get_provider()` returns for that request. `DEFAULT_LLM_PROVIDER` in `.env` only affects the
health check default; every chat request is explicit about which provider to use, so routing is
stateless and per-request.

## SSE streaming
`POST /api/chat` returns a `StreamingResponse` with `media_type="text/event-stream"`. Events:
- `token` — `{ text }` incremental content as it's generated.
- `artifact` — `{ id, artifact_type, title, content }` emitted once, if the model wrapped output in an `<artifact>` tag.
- `done` — `{ message_id, sources, artifact_id }` marks stream completion and persists the final assistant message.
- `error` — `{ detail }` for provider failures, sent instead of `done`.

The frontend (`lib/api.ts streamChat`) reads the raw `ReadableStream`, splits on blank-line-delimited
SSE frames, and dispatches to handlers that update React state incrementally (`useChatStream`).

## Artifact security
- The LLM is instructed to wrap generated content in `<artifact type="markdown|html" title="...">...</artifact>`.
- `app/skills/artifact_generator.py` extracts this via regex server-side; only `markdown` or `html`
  types are recognized.
- On the frontend, HTML artifacts are never rendered directly: `SandboxedIframe.tsx` runs the HTML
  through `DOMPurify.sanitize()` first, then injects it via `srcDoc` into an `<iframe sandbox="allow-scripts">`.
  `allow-same-origin` is deliberately omitted so the iframe is treated as an opaque, unique origin
  with no access to the parent app's cookies, localStorage, DOM, or origin. Markdown artifacts are
  rendered with `react-markdown` + `remark-gfm`, which never generates raw HTML from user content.
