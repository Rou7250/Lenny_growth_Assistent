# PRD: Lenny Growth Assistant

## Problem
Product managers and growth leaders learn a huge amount from Lenny's Podcast, but that
knowledge is locked inside hours of transcript audio/text. There's no fast way to ask a
specific question ("how do I improve activation for a B2B SaaS product?") and get a grounded,
attributable answer instead of a generic LLM hallucination.

## Target user
Product managers, growth PMs, and startup founders who listen to (or want to mine) Lenny's
Podcast for tactical advice, and who need to quickly produce shareable content based on it.

## Goals
- Ground every answer strictly in retrieved transcript chunks — never hallucinate.
- Provide clear source attribution (episode, guest, timestamp) for every claim.
- Support both local (Ollama) and cloud (Groq) inference, switchable per request.
- Generate a publishable ~1,250-word Ship 30 for 30 style article from transcript context.
- Render generated content (Markdown or HTML) safely in an artifact viewer.

## Non-goals
- Not a general-purpose chatbot; out-of-domain questions are explicitly declined.
- Not a transcript hosting/distribution service — ingestion is local/manual.
- Not a multi-tenant SaaS with auth in this version — single-user local/dev deployment.

## User stories
- As a PM, I ask "How do I run a PMF survey?" and get an answer citing the exact episode/guest.
- As a growth lead, I ask an out-of-domain question and get a clear "insufficient information" response instead of a fabricated answer.
- As a content creator, I switch to Ship 30 mode and get a ready-to-edit article grounded in real transcript insights, viewable/exportable from the artifact panel.
- As a developer, I switch between Ollama and Groq without touching any RAG or prompt logic.

## Success metrics
- 0% hallucinated citations in manual QA (every citation traceable to a stored chunk).
- Out-of-domain questions correctly trigger the "insufficient information" response.
- Ship 30 articles land within ~10% of the 1,250-word target.
- Provider switch requires no code change, only a request parameter.

## Risks
- Small local Llama models (via Ollama) may follow grounding instructions less reliably than larger cloud models — mitigated by strict system prompting and post-hoc "insufficient context" gating done in code, not just prompting.
- Poor transcript formatting could produce noisy chunks/timestamps — mitigated by a documented ingestion frontmatter/timestamp format.
- Embedding model (MiniLM) is small/fast but less accurate than larger embedding models — acceptable trade-off for local-first operation.

## Trade-offs
- Chose pgvector + Postgres over a dedicated vector DB for operational simplicity (one datastore for chunks, sessions, and messages).
- Chose SSE over WebSockets for streaming — simpler, unidirectional, sufficient for this use case.
- Chose word-count-based chunking (proxy for tokens) to avoid adding a tokenizer dependency.
