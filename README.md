# RAG-L1-Support-Bot

**TRL5 Prototype** — RAG-based Technical Support Bot for Level 1 queries.

## Overview

Prototype that automates Level 1 support queries using semantic search over technical manuals stored in Pinecone, with GPT-powered response generation.

### Features

- **HU-01**: Ingest and process technical manuals (PDF/Markdown) → Pinecone
- **HU-02**: Automatic synchronization via file watcher (watchdog)
- **HU-04**: Web interface with FastAPI — `/chat` endpoint, < 5s response

### Architecture

```
Manuales (PDF/MD) → File Watcher → Pinecone Assistant
                                           ↓
User Query → FastAPI /chat → Pinecone Assistant → Response (<5s)
```

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/YOUR_ORG/RAG-L1-Support-Bot.git
cd RAG-L1-Support-Bot
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials:
# PINECONE_API_KEY=your_key
# PINECONE_ASSISTANT_NAME=rag-l1-support
```

### 3. Create Pinecone Assistant

```bash
# In Pinecone console or via API:
pc = Pinecone(api_key="YOUR_KEY")
assistant = pc.assistant.create_assistant(
    assistant_name="rag-l1-support",
    instructions="Use the uploaded documents to answer technical support questions."
)
```

### 4. Ingest Manuals

```bash
python scripts/ingest_manual.py --file manuals/guia.pdf --category networking
python scripts/ingest_manual.py --file manuals/faq.md --category faq
```

### 5. Run the Server

```bash
python -m app.main
# or: uvicorn app.main:app --reload
```

### 6. Run the File Watcher (optional — for auto-sync)

```bash
python -m sync.watcher
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/chat` | Chat with the assistant |
| GET | `/docs` | OpenAPI documentation |

### Example Chat Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cómo reseteo la contraseña de admin?"}'
```

### Example Response

```json
{
  "answer": "Para resetear la contraseña de admin, sigue estos pasos...",
  "sources": [
    {
      "name": "guia.pdf",
      "pages": [3, 4],
      "metadata": {"category": "networking"}
    }
  ],
  "finish_reason": "stop",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 85,
    "total_tokens": 235
  }
}
```

## Project Structure

```
rag-l1-support-bot/
├── app/
│   ├── main.py           # FastAPI app
│   └── rag.py            # RAG logic
├── sync/
│   ├── watcher.py        # File watcher
│   └── assistant_client.py
├── scripts/
│   └── ingest_manual.py  # CLI ingestion
├── docs/
│   └── FLOW.md          # Architecture diagram
├── manuals/             # Source documents (gitignored)
├── openspec/            # SDD artifacts
├── requirements.txt
└── README.md
```

## Testing

```bash
pytest tests/ -v
```

## Metrics (TRL5)

- **Response time**: < 5 seconds end-to-end
- **Precision**: ≥ 90% (via correct citations)
- **Sync latency**: < 10 seconds from file change to query

## Stack

- **Database**: Pinecone (Assistant API)
- **Framework**: FastAPI
- **Sync**: watchdog
- **LLM**: GPT-4o via Pinecone Assistant

## License

MIT