# Design: RAG-L1-Support-Bot Core

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                   │
│                                                                     │
│  ┌──────────┐    ┌─────────────┐    ┌─────────────────┐            │
│  │ Manuals  │───▶│ File Watcher│───▶│ Pinecone Assistant│           │
│  │ PDF/MD   │    │  (watchdog) │    │    SDK           │            │
│  └──────────┘    └─────────────┘    └────────┬────────┘            │
│                                               │                     │
│  ┌──────────┐    ┌─────────────┐    ┌────────▼────────┐            │
│  │  User    │───▶│  FastAPI   │───▶│  Assistant       │           │
│  │  Query   │    │  /chat     │    │  chat()          │            │
│  └──────────┘    └─────────────┘    └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. `app/main.py` — FastAPI Application

```
FastAPI app
├── GET /health → {status, assistant}
├── POST /chat  → {answer, sources, citations}
└── lifespan startup/shutdown for assistant init
```

**Key Decision:** Usar lifespan events para inicializar el assistant una sola vez.

### 2. `app/rag.py` — RAG Logic

```python
async def query_assistant(message: str) -> dict:
    # 1. Chat with Pinecone Assistant
    # 2. Extract answer + citations
    # 3. Format response
    return {answer, sources, citations, usage}
```

**Key Decision:** No hacer retrieval manual — delegar a Pinecone Assistant que hace RAG internally.

### 3. `sync/watcher.py` — File Watcher

```python
class ManualWatcher(FileSystemEventHandler):
    def __init__(self, assistant_client):
        self.debounce_seconds = 2

    def on_modified(self, event):
        # Debounce → re-ingest
```

**Key Decision:** Debounce de 2 segundos para evitar múltiples triggers por auto-save.

### 4. `sync/assistant_client.py` — Pinecone Assistant Wrapper

```python
class AssistantClient:
    def __init__(self, api_key, assistant_name):
        self.pc = Pinecone(api_key=api_key)
        self.assistant = self.pc.assistant.Assistant(assistant_name)

    def upload_file(self, file_path, metadata):
        return self.assistant.upload_file(file_path, metadata)

    def chat(self, messages):
        return self.assistant.chat(messages)
```

### 5. `scripts/ingest_manual.py` — CLI Script

```bash
python scripts/ingest_manual.py --file manuals/guia.pdf
```

## File Structure

```
rag-l1-support-bot/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   └── rag.py           # RAG logic
├── sync/
│   ├── __init__.py
│   ├── watcher.py       # FileSystemEventHandler
│   └── assistant_client.py
├── scripts/
│   └── ingest_manual.py # CLI for manual ingestion
├── manuals/            # Source documents (gitignored)
├── docs/
│   └── FLOW.md         # Data flow diagram
├── openspec/
│   ├── config.yaml
│   ├── specs/rag-bot/spec.md
│   └── changes/rag-l1-support-bot/
│       ├── proposal.md
│       ├── specs/rag-bot/spec.md
│       ├── design.md
│       ├── tasks.md
│       └── state.yaml
├── requirements.txt
└── README.md
```

## Environment Variables

```bash
PINECONE_API_KEY=...
PINECONE_ASSISTANT_NAME=rag-l1-support
MANUALS_DIR=manuals/
```

## Dependencies

```
pinecone>=5.0.0
pinecone-plugin-assistant
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
watchdog>=3.0.0
python-multipart>=0.0.6
```

## Key Decisions

1. **Pinecone Assistant over vectors + LangChain**
   - Rationale: ~70% menos código, chunking y embedding automático
   - Tradeoff: Menos control sobre embedding, pero TRL5 prototype acceptable

2. **watchdog para sync**
   - Rationale: Simple, cross-platform, no infrastructure
   - Alternative: GitHub webhooks — más complejo, requiere GitHub Actions

3. **FastAPI sobre Flask**
   - Rationale: Type safety, async, auto OpenAPI docs
   - Tradeoff: Slightly more verbose for simple endpoints

4. **Debounce 2s para file watcher**
   - Rationale: Editors auto-save pueden generar múltiples eventos
   - Tradeoff: 2s delay acceptable para sync de documentation

## Metrics

- **Response time:** < 5 segundos end-to-end
- **Precision:** ≥ 90% (medido via citations correctas)
- **Sync latency:** < 10 segundos desde cambio hasta query reflejada