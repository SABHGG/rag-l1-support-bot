# RAG-L1-Support-Bot — Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────────┐    ┌──────────────────────┐
│  Manuales   │    │  Pinecone       │    │  FastAPI Server       │
│  PDF/MD     │───▶│  Assistant      │◀───│  /chat endpoint       │
│  en         │    │  SDK            │    │  POST {message}       │
│  manuals/   │    │                 │    │                       │
└─────────────┘    └─────────────────┘    └──────────────────────┘
       │                   ▲                       │
       │                   │                       │
       ▼                   │                       ▼
┌─────────────┐    ┌─────────────────┐    ┌──────────────────────┐
│  watchdog   │    │  Assistant      │    │  User Query          │
│  File       │───▶│  chat()         │───▶│  Natural Language    │
│  Watcher    │    │  (RAG intern)   │    │  < 5 seconds         │
└─────────────┘    └─────────────────┘    └──────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION FLOW                            │
│                                                              │
│  1. User runs: python scripts/ingest_manual.py --file X.pdf   │
│  2. assistant_client.upload_file()                           │
│  3. Pinecone Assistant:                                      │
│     a. Chunking (automatic)                                  │
│     b. Embedding (via hosted model)                          │
│     c. Indexing (in Pinecone)                                │
│  4. Done — ready for queries                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      SYNC FLOW                               │
│                                                              │
│  1. File watcher detects change in manuals/                  │
│  2. Debounce 2 seconds (avoid multi-trigger from auto-save) │
│  3. Re-upload modified file via assistant.upload_file()     │
│  4. Log event to sync/sync.log                              │
│  5. Next query reflects updated content                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      QUERY FLOW                              │
│                                                              │
│  1. User POST /chat {"message": "¿Cómo reseteo?"}           │
│  2. FastAPI calls rag.query_assistant()                      │
│  3. AssistantClient.chat() sends to Pinecone Assistant      │
│  4. Pinecone Assistant:                                      │
│     a. Embeds query                                         │
│     b.Retrieves relevant chunks                             │
│     c. Generates response with GPT                          │
│  5. Return: {answer, sources, citations, usage}              │
│                                                              │
│  Response time: < 5 seconds end-to-end                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    METRICS (TRL5)                            │
│                                                              │
│  • Response Time: < 5 seconds (target)                       │
│  • Precision: ≥ 90% (measured via correct citations)         │
│  • Sync Latency: < 10 seconds from file change to query      │
│  • Chunk Coherence: Contextual chunks maintained             │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| `manuals/` | Source PDFs and Markdown files |
| `scripts/ingest_manual.py` | CLI for manual ingestion |
| `sync/watcher.py` | FileSystemEventHandler for auto-sync |
| `sync/assistant_client.py` | Pinecone Assistant SDK wrapper |
| `app/main.py` | FastAPI app with /health and /chat |
| `app/rag.py` | Query formatting and citation extraction |