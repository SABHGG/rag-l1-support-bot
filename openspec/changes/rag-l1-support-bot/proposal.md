# Proposal: RAG-L1-Support-Bot Core

## Change Name
`rag-l1-support-bot`

## 1. Motivation

Automatizar consultas de Nivel 1 mediante búsqueda semántica en manuales corporativos. El sistema debe:
- Procesar manuales técnicos (PDF/Markdown) y convertirlos en vectores indexados en Pinecone
- Sincronizar automáticamente cuando los manuales fuente cambien
- Entregar respuestas coherentes en < 5 segundos via interfaz Web (FastAPI)

## 2. Capabilities

### HU-01: Ingesta y Procesamiento de Conocimiento
- Chunking de PDFs y Markdown con coherencia contextual
- Indexación en Pinecone (integrated embedding)
- Metadata tracking por fuente y categoría

### HU-02: Módulo de Sincronización Automática
- File watcher que detecte cambios en archivos fuente
- Re-ingestión automática al detectar modificaciones
- Logging de eventos de sincronización

### HU-04: Interfaz de Respuesta al Usuario Final
- FastAPI endpoint `/chat` para preguntas en lenguaje natural
- Recupera contexto de Pinecone Assistant
- Genera respuesta conGPT, referencing fuentes
- Tiempo de respuesta < 5s

## 3. Approach

**Arquitectura:** Pinecone Assistant API (maneja chunking + embedding + RAG nativamente)

```
Manuales (PDF/MD)
      ↓
File Watcher (watchdog)
      ↓
Pinecone Assistant SDK (upload_file)
      ↓
FastAPI /chat → Pinecone Assistant → Response
```

**Decisiones clave:**
- Usar Pinecone Assistant en lugar de vectors + LangChain → menos código, más rápido de prototipar
- FastAPI por typing superior y async nativo
- watchdog para sync basada en filesystem events

## 4. Rollback Plan

Si Pinecone Assistant no cumple los requisitos de precisión:
- Cambiar a enfoque vectors + LangChain
- Mantener el mismo endpoint `/chat`
- Re-ingerir datos con embedding model externo