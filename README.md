# Lenny Growth Assistant

A grounded RAG (Retrieval-Augmented Generation) assistant built over Lenny's Podcast transcripts for product managers and growth leaders, featuring a **Ship 30 for 30** article-generation mode and a secure Markdown/HTML artifact preview panel.

---

## Key Features

- **Strictly Grounded Retrieval**: Answers are grounded directly in podcast transcript chunks with `[Episode: Guest, Timestamp]` citations.
- **Hallucination Prevention**: Out-of-domain or ungrounded questions receive an explicit "insufficient information" response rather than fabricated answers.
- **Flexible LLM Inference**: Seamlessly switch between local inference (**Ollama**) and cloud inference (**Groq**) per request.
- **Ship 30 for 30 Mode**: Transforms transcript context into high-impact ~1,250-word atomic articles rendered in an interactive side-panel.
- **Modern Stack**: FastAPI backend with asyncpg + pgvector, React + TypeScript + Tailwind frontend with real-time Server-Sent Events (SSE) streaming.

---

## Prerequisites

- **Python**: 3.11 or 3.12 *(Recommended: Python 3.12. Avoid Python 3.14+ pre-releases due to C/Rust native extension compatibility)*
- **Node.js**: 18+ or 20+ and npm
- **Database**: PostgreSQL 16 with the `pgvector` extension enabled
- **LLM Provider** (at least one):
  - **Ollama** installed locally (model: `llama3.2:3b`)
  - **Groq API Key** (for fast cloud inference with `llama-3.1-70b-versatile`)
- *(Alternative)* **Docker & Docker Compose** for all-in-one containerized deployment.

---

## Environment Configuration

Create a `.env` file in the project root by copying `.env.example`:

```bash
cp .env.example .env
```

### Key Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string with asyncpg | `postgresql+asyncpg://lenny:lenny@localhost:5432/lenny_growth` |
| `DEFAULT_LLM_PROVIDER` | Default provider (`ollama` or `groq`) | `groq` |
| `GROQ_API_KEY` | Your Groq Cloud API key (server-side only) | `gsk_...` |
| `GROQ_MODEL` | Groq model name | `llama-3.1-70b-versatile` |
| `OLLAMA_BASE_URL` | Ollama HTTP endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model tag | `llama3.2:3b` |
| `EMBEDDING_MODEL` | SentenceTransformer model | `all-MiniLM-L6-v2` |
| `TOP_K` | Number of chunks retrieved per query | `5` |
| `SIMILARITY_THRESHOLD` | Cosine similarity cutoff | `0.65` |
| `CORS_ORIGINS` | Permitted frontend origins | `http://localhost:5173` |
| `VITE_API_BASE_URL` | Frontend API target | `http://localhost:8000` |

> [!NOTE]
> `GROQ_API_KEY` is loaded strictly server-side by the backend and is never exposed to or bundled into the frontend.

---

## Running Locally

### 1. Backend Setup

#### On Windows (PowerShell):
```powershell
cd backend

# Create virtual environment with Python 3.12
py -3.12 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Ingest transcript data into PostgreSQL / pgvector
python scripts/ingest.py

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

*(Note: If PowerShell blocks script execution, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before activating).*

#### On macOS / Linux (Bash):
```bash
cd backend

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ingest transcripts
python scripts/ingest.py

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

The backend will be live at:
- **API**: http://localhost:8000
- **Interactive Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

### 2. Frontend Setup

In a **separate terminal tab**:

```powershell
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

The frontend application will be live at:
- **UI**: [http://localhost:5173](http://localhost:5173)

---

## Running with Docker Compose (Alternative)

If you have Docker Desktop installed, you can launch all services (PostgreSQL + pgvector, Ollama, Backend, and Frontend) with a single command:

```bash
docker-compose up --build
```

### Post-startup steps for Docker:
1. **Pull the Ollama model**:
   ```bash
   docker exec -it lenny-growth-assistant-ollama-1 ollama pull llama3.2:3b
   ```
2. **Ingest transcript data**:
   ```bash
   docker exec -it lenny-growth-assistant-backend-1 python scripts/ingest.py
   ```

---

## Transcript Ingestion

1. Place `.md` or `.txt` transcript files into the `agent_transcripts/` directory. Transcripts must include frontmatter metadata:
   ```markdown
   ---
   episode_title: How Superhuman Builds Product
   guest_name: Rahul Vohra
   publication_date: 2023-05-01
   ---
   [00:00] Intro text...
   [05:30] Discussion on finding product-market fit...
   ```
2. Run the ingestion pipeline:
   ```bash
   python scripts/ingest.py
   ```
   - Chunks text into ~650-word segments with ~90-word overlap.
   - Generates 384-dimensional dense embeddings using `all-MiniLM-L6-v2`.
   - Stores vectors and metadata in `transcript_chunks` with hash-based deduplication (safe to re-run).

A sample transcript is provided in `agent_transcripts/sample-superhuman-pmf.md`.

---

## LLM Provider Setup

### Option A: Groq (Cloud — Fastest)
1. Generate an API key at [console.groq.com](https://console.groq.com).
2. Set `GROQ_API_KEY` in your `.env` file.
3. Select **"Groq — Cloud"** in the UI provider dropdown or set `DEFAULT_LLM_PROVIDER=groq`.

### Option B: Ollama (Local — Offline)
1. Install [Ollama](https://ollama.com).
2. Pull the model:
   ```bash
   ollama pull llama3.2:3b
   ```
3. Ensure Ollama is running at `http://localhost:11434`.
4. Select **"Ollama — Local"** in the UI dropdown.

---

## Testing

Run unit and integration tests from the `backend/` directory:

```bash
cd backend
pytest
```

Tests cover:
- Retrieval relevance, similarity thresholding, and empty result handling
- Provider switching (Ollama vs. Groq) and streaming SSE responses
- Session management, error propagation, and `/api/health` status

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status (DB, pgvector, Ollama/Groq) |
| `POST` | `/api/sessions` | Create a new chat session |
| `GET` | `/api/sessions` | List all historical sessions |
| `GET` | `/api/sessions/{id}` | Fetch session history and messages |
| `POST` | `/api/chat` | Stream SSE responses (`token`, `artifact`, `done`, `error`) |

For comprehensive architecture details and specifications, refer to [docs/PRD.md](file:///d:/lenny-growth-assistant/docs/PRD.md), [docs/architecture.md](file:///d:/lenny-growth-assistant/docs/architecture.md), and [docs/design.md](file:///d:/lenny-growth-assistant/docs/design.md).
