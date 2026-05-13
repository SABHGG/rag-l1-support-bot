# Tasks: RAG-L1-Support-Bot Core

## Implementation Phases

### Phase 1: Project Setup
- [ ] 1.1 Create `requirements.txt` with all dependencies
- [ ] 1.2 Create `app/__init__.py`
- [ ] 1.3 Create `sync/__init__.py`
- [ ] 1.4 Create `scripts/__init__.py`
- [ ] 1.5 Create `.env.example` with required env vars
- [ ] 1.6 Create `manuals/` directory (gitignored)

### Phase 2: Pinecone Assistant Client
- [ ] 2.1 Implement `sync/assistant_client.py`
  - `AssistantClient` class with `upload_file()`, `chat()`
  - Initialize from env vars
- [ ] 2.2 Add error handling for API key missing

### Phase 3: FastAPI Application
- [ ] 3.1 Implement `app/main.py`
  - FastAPI app with lifespan
  - GET `/health` endpoint
  - POST `/chat` endpoint
- [ ] 3.2 Implement `app/rag.py`
  - `query_assistant()` function
  - Response formatting
- [ ] 3.3 Add OpenAPI docs at `/docs`

### Phase 4: File Watcher (Sync)
- [ ] 4.1 Implement `sync/watcher.py`
  - `ManualWatcher` class extending `FileSystemEventHandler`
  - 2-second debounce logic
  - Ignore `.tmp`, `~` files
- [ ] 4.2 Add logging to `sync/sync.log`

### Phase 5: Ingestion Script
- [ ] 5.1 Implement `scripts/ingest_manual.py`
  - CLI with `--file` argument
  - Support PDF and Markdown
  - Report chunk count

### Phase 6: Documentation
- [ ] 6.1 Create `docs/FLOW.md` with architecture diagram
- [ ] 6.2 Create `README.md` with setup instructions
- [ ] 6.3 Create `LICENSE` and `.gitignore`

### Phase 7: Testing
- [ ] 7.1 Create `tests/test_rag.py` with pytest
- [ ] 7.2 Create `tests/test_watcher.py`
- [ ] 7.3 Verify all specs pass

## Delivery Notes

**Decision needed before apply:** No
**Chained PRs recommended:** No
**400-line budget risk:** Low