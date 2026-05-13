# Spec: RAG-L1-Support-Bot Core

## Domain: rag-bot

---

## HU-01: Ingesta y Procesamiento de Conocimiento

El sistema SHALL tomar manuales técnicos (PDF/Markdown), dividirlos en fragmentos (chunking) y convertirlos en vectores de alta dimensionalidad indexados en Pinecone.

### Scenario: Upload PDF manual successfully

**Given** un archivo PDF de manual técnico existe en `manuals/`
**When** el usuario ejecuta `python scripts/ingest_manual.py --file manual.pdf`
**Then** el sistema SHALL split el PDF en chunks coherentes
**And** SHALL upload cada chunk a Pinecone Assistant
**And** SHALL reportar количество chunks ingestados

### Scenario: Upload Markdown manual successfully

**Given** un archivo Markdown existe en `manuals/`
**When** el usuario ejecuta `python scripts/ingest_manual.py --file guia.md`
**Then** el sistema SHALL leer el contenido Markdown
**And** SHALL upload el contenido a Pinecone Assistant
**And** SHALL mantener los headers como metadata

---

## HU-02: Módulo de Sincronización Automática

El sistema SHALL detectar si un manual ha sido editado y actualizar el vector correspondiente sin intervención manual.

### Scenario: File watcher detects change

**Given** el file watcher está corriendo con `python -m sync.watcher`
**And** un archivo en `manuals/` cambia
**When** watchdog detecta el evento de modificación
**Then** el sistema SHALL esperar 2 segundos (debounce)
**And** SHALL re-ingerir el archivo modificado

### Scenario: File watcher logs sync event

**Given** el file watcher detecta un cambio
**When** la re-ingestión completa
**Then** el sistema SHALL loguear timestamp + filename a `sync/sync.log`
**And** SHALL mostrar "Synced: {filename}" en stdout

### Scenario: File watcher ignores temporary files

**Given** el file watcher está activo
**When** un archivo temporal (`.tmp`, `~`) es modificado
**Then** el sistema SHALL ignorar el evento

---

## HU-04: Interfaz de Respuesta al Usuario Final

El sistema SHALL entregar respuestas coherentes en menos de 5 segundos via interfaz Web.

### Scenario: User asks question via /chat endpoint

**Given** Pinecone Assistant tiene documentos cargados
**When** usuario POST a `/chat` con `{"message": "¿Cómo reseteo la contraseña?"}`
**Then** el sistema SHALL recuperar contexto relevante de Pinecone
**And** SHALL generar respuesta con GPT
**And** SHALL incluir citations del documento fuente
**And** SHALL responder en < 5 segundos

### Scenario: /chat returns proper JSON structure

**Given** una pregunta válida es enviada a `/chat`
**When** el sistema procesa la request
**Then** la respuesta SHALL ser JSON con `{"answer": "...", "sources": [...]}`
**And** SHALL incluir `finish_reason: "stop"`
**And** SHALL incluir `usage` con token counts

### Scenario: /chat handles empty context

**Given** la query no encuentra contexto relevante en Pinecone
**When** el sistema procesa la request
**Then** SHALL responder con "No encontré información relevante en los manuales."
**And** SHALL still return JSON válido

### Scenario: Health check endpoint works

**Given** el servidor FastAPI está corriendo
**When** usuario GET a `/health`
**Then** SHALL retornar `{"status": "ok", "assistant": "ready"}`