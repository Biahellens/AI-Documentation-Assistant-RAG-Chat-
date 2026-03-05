# AI-Documentation-Assistant-RAG-Chat

> Intelligent chat over technical documentation using Retrieval-Augmented Generation (RAG)

Upload PDFs or Markdown files, ask questions, and get answers grounded in your own documents — with full conversation memory, token logging, and source attribution.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                   │
│  Upload Docs  ──►  Document List  ──►  Chat Interface       │
└────────────────────────────┬────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────┐
│                     Backend (FastAPI)                        │
│                                                             │
│   POST /upload          POST /chat           GET /docs      │
│        │                     │                              │
│   ┌────▼────┐          ┌─────▼──────┐                      │
│   │Ingestion│          │ RAG Service│                       │
│   │Pipeline │          │            │                       │
│   │         │          │ 1. Embed Q │                       │
│   │1. Parse │          │ 2. Retrieve│                       │
│   │2. Chunk │          │ 3. Window  │                       │
│   │3. Embed │          │ 4. Prompt  │                       │
│   │4. Store │          │ 5. Generate│                       │
│   └────┬────┘          └─────┬──────┘                      │
│        │                     │                              │
│   ┌────▼─────────────────────▼──────┐                      │
│   │        Embedding Model           │                      │
│   │   sentence-transformers          │                      │
│   │   all-MiniLM-L6-v2  (384-dim)   │                      │
│   └────────────────┬────────────────┘                      │
│                    │                                        │
│   ┌────────────────▼────────────────┐                      │
│   │         Vector Store            │                      │
│   │   ChromaDB (cosine similarity)  │                      │
│   └─────────────────────────────────┘                      │
│                    │                                        │
│   ┌────────────────▼────────────────┐                      │
│   │          LLM (optional)         │                      │
│   │   OpenAI gpt-4o-mini            │                      │
│   └─────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline Explained

### 1. Ingestion (Offline)

When a document is uploaded:

```
PDF / Markdown
     │
     ▼
Text Extraction  (pypdf for PDF, UTF-8 for .md)
     │
     ▼
Chunking  (sliding window, 512 tokens, 64 overlap)
     │
     ▼
Embedding  (all-MiniLM-L6-v2 → 384-dim vectors)
     │
     ▼
ChromaDB  (persistent, cosine similarity index)
```

### 2. Retrieval (Online, per query)

```
User Question
     │
     ▼
Embed Question  (same model as ingestion — critical!)
     │
     ▼
Top-K Similarity Search  (K=5, cosine distance in Chroma)
     │
     ▼
Retrieved Chunks + Metadata (filename, chunk_index)
```

### 3. Generation

```
Retrieved Chunks + Conversation History (last 6 turns)
     │
     ▼
Prompt Assembly
     │
     ▼
LLM (gpt-4o-mini, temp=0.2)
     │
     ▼
Answer + Sources + Token Usage
```

---

## Chunking Strategy

### Approach: Sentence-Aware Sliding Window

```python
CHUNK_SIZE    = 512   # ~380 words per chunk
CHUNK_OVERLAP = 64    # ~48 words of overlap
```

**Why 512 tokens?**
- Large enough to contain a complete idea or paragraph
- Small enough that retrieved chunks are focused and relevant
- Sweet spot validated empirically for technical documentation

**Why 64-token overlap?**
- Prevents losing context at chunk boundaries
- If a sentence spans two chunks, at least one chunk contains it fully
- 12% overlap — beyond 20% gives diminishing returns

**Trade-offs considered:**

| Strategy | Quality | Speed | Complexity |
|---|---|---|---|
| **Sliding window (chosen)** | ✅ Good | ✅ Fast | ✅ Simple |
| Semantic chunking | ⭐ Best | ❌ Slow | ❌ Complex |
| Paragraph-based | ⚠️ Uneven sizes | ✅ Fast | ✅ Simple |
| Recursive char split | ✅ Good | ✅ Fast | ⚠️ Medium |

**For production:** consider `tiktoken` for exact token counting instead of word approximation (~1.3 words/token for English technical text).

---

## Embedding Model Choice

### Chosen: `sentence-transformers/all-MiniLM-L6-v2`

| Property | Value |
|---|---|
| Dimensions | 384 |
| Parameters | 22M |
| Max sequence | 256 tokens |
| Inference speed | ~14k sentences/sec on CPU |
| License | Apache 2.0 (free) |

**Why not OpenAI `text-embedding-ada-002`?**

| | all-MiniLM-L6-v2 | ada-002 |
|---|---|---|
| Cost | Free | $0.0001/1K tokens |
| Dimensions | 384 | 1536 |
| Latency | Local, ~5ms | Network, ~200ms |
| Quality (MTEB) | 56.3 | 60.5 |
| Privacy | ✅ On-premise | ❌ Data sent to OpenAI |
| Cold start | ~2s (model load) | None |

**Verdict:** For most technical documentation use cases, the ~4 point MTEB gap is not noticeable. The free, private, fast local model wins for this project. Swap to ada-002 if you need maximum retrieval quality at scale.

---

## Memory Window

Conversation history is truncated to the last **N turns** (default: 6 = 3 user + 3 assistant messages) before being included in the prompt.

**Why not unlimited history?**
- LLM context windows have token limits
- Old turns are usually irrelevant to the current question
- Cost: every extra turn = extra tokens = extra cost

**Why 6 turns?**
- Enough to follow multi-step reasoning ("as you mentioned above...")
- Small enough to leave room for retrieved context

**Production upgrade:** swap the in-memory `_sessions` dict for Redis with TTL expiry.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API | FastAPI | Async, type-safe, auto docs |
| Embeddings | sentence-transformers | Free, local, high quality |
| Vector DB | ChromaDB | Persistent, metadata filtering, easy setup |
| LLM | OpenAI gpt-4o-mini | Fast, cheap, good at instruction-following |
| Frontend | Next.js 14 + Tailwind | App Router, TypeScript, rapid UI |

---

## Quick Start

### With Docker Compose (recommended)

```bash
git clone <your-repo>
cd rag-chat

# Optional: add OpenAI key for LLM answers
echo "OPENAI_API_KEY=sk-..." > .env

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### Without Docker

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit if needed
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
rag-chat/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS
│   │   ├── api/
│   │   │   ├── chat.py          # POST /api/chat
│   │   │   ├── documents.py     # POST /api/documents/upload
│   │   │   └── health.py        # GET /health
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   ├── embeddings.py    # Embedding model wrapper
│   │   │   ├── chunker.py       # Sliding window chunker
│   │   │   └── vector_store.py  # Chroma CRUD
│   │   ├── services/
│   │   │   ├── ingestion.py     # Parse → chunk → embed → store
│   │   │   ├── rag.py           # Retrieve → prompt → generate
│   │   │   └── token_logger.py  # JSONL usage log
│   │   └── models/
│   │       └── schemas.py       # Pydantic request/response models
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx         # Main chat UI
│       │   └── layout.tsx
│       └── lib/
│           └── api.ts           # Typed API client
├── docker-compose.yml
└── README.md
```

---

## Features

- **Document upload** — PDF and Markdown support
- **Semantic search** — finds relevant chunks even without exact keyword match
- **Conversation memory** — sliding window keeps last 6 turns in context
- **Doc filtering** — pin a specific document to restrict retrieval scope
- **Token logging** — every request is logged to `logs/token_usage.jsonl`
- **Source attribution** — each answer shows which chunks were used
- **Works offline** — retrieval works without any API key; only generation needs OpenAI

---

## Potential Improvements

- **Reranking** — add a cross-encoder reranker (e.g. `ms-marco-MiniLM`) after retrieval for higher precision
- **Hybrid search** — combine dense (vector) + sparse (BM25) retrieval
- **Streaming** — stream LLM tokens to the frontend for lower perceived latency
- **Auth** — add user accounts so each user has their own document namespace
- **Redis sessions** — replace in-memory history with persistent Redis sessions
- **Eval harness** — add RAGAS metrics (faithfulness, answer relevancy) for automated quality testing
