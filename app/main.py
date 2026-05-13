"""FastAPI application for RAG-L1-Support-Bot."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from app.rag import query_assistant, check_assistant_status

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    yield


app = FastAPI(
    title="RAG-L1-Support-Bot",
    description="RAG Prototype for Technical Support - TRL5",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-4o"


class ChatResponse(BaseModel):
    answer: str
    sources: list
    finish_reason: str
    usage: dict


@app.get("/health")
async def health():
    """Health check endpoint."""
    return await check_assistant_status()


@app.get("/", response_class=HTMLResponse)
async def index():
    """Web interface for chatting with the assistant."""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RAG-L1 Support Bot</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                width: 100%;
                max-width: 800px;
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 24px 32px;
            }
            .header h1 { font-size: 1.5rem; margin-bottom: 4px; }
            .header p { opacity: 0.9; font-size: 0.9rem; }
            .chat-area {
                height: 400px;
                overflow-y: auto;
                padding: 24px 32px;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }
            .message {
                padding: 12px 16px;
                border-radius: 12px;
                max-width: 80%;
                line-height: 1.5;
            }
            .message.user {
                background: #667eea;
                color: white;
                align-self: flex-end;
                border-bottom-right-radius: 4px;
            }
            .message.assistant {
                background: #f1f3f5;
                color: #333;
                align-self: flex-start;
                border-bottom-left-radius: 4px;
            }
            .message.error {
                background: #fff5f5;
                color: #c53030;
                border: 1px solid #fc8181;
            }
            .message.sources {
                background: #f0fff4;
                border: 1px solid #68d391;
                font-size: 0.85rem;
            }
            .sources-list { margin-top: 8px; }
            .source-item { margin: 4px 0; }
            .input-area {
                padding: 24px 32px;
                border-top: 1px solid #eee;
                display: flex;
                gap: 12px;
            }
            .input-area input {
                flex: 1;
                padding: 14px 18px;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                font-size: 1rem;
                outline: none;
                transition: border-color 0.2s;
            }
            .input-area input:focus { border-color: #667eea; }
            .input-area button {
                padding: 14px 28px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.1s, opacity 0.2s;
            }
            .input-area button:hover { opacity: 0.9; }
            .input-area button:active { transform: scale(0.98); }
            .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
            .loading {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid white;
                border-radius: 50%;
                border-top-color: transparent;
                animation: spin 0.8s linear infinite;
                margin-right: 8px;
                vertical-align: middle;
            }
            @keyframes spin { to { transform: rotate(360deg); } }
            .empty-state {
                text-align: center;
                color: #a0aec0;
                padding: 60px 20px;
            }
            .empty-state svg { width: 64px; height: 64px; margin-bottom: 16px; opacity: 0.5; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>RAG-L1 Support Bot</h1>
                <p>Asistente de Soporte Técnico — Preguntá en lenguaje natural</p>
            </div>
            <div class="chat-area" id="chatArea">
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                    </svg>
                    <p>Escribí tu pregunta abajo para comenzar</p>
                </div>
            </div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Escribí tu pregunta..." autocomplete="off">
                <button id="sendBtn" onclick="sendMessage()">Enviar</button>
            </div>
        </div>
        <script>
            const chatArea = document.getElementById('chatArea');
            const messageInput = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });

            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;

                addMessage(message, 'user');
                messageInput.value = '';
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<span class="loading"></span>Respondiendo...';

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message })
                    });
                    const data = await response.json();

                    if (!response.ok) throw new Error(data.detail || 'Error interno');

                    addMessage(data.answer, 'assistant');
                    if (data.sources && data.sources.length > 0) {
                        let sourcesHtml = '<div class="sources-list">';
                        data.sources.forEach(s => {
                            sourcesHtml += `<div class="source-item">📄 <strong>${s.name}</strong>${s.pages ? ' - pág. ' + s.pages.join(', ') : ''}</div>`;
                        });
                        sourcesHtml += '</div>';
                        addMessage('Fuentes: ' + sourcesHtml, 'assistant sources');
                    }
                } catch (err) {
                    addMessage(err.message, 'error');
                } finally {
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = 'Enviar';
                }
            }

            function addMessage(text, type) {
                const div = document.createElement('div');
                div.className = 'message ' + type;
                div.innerHTML = text;
                chatArea.appendChild(div);
                chatArea.scrollTop = chatArea.scrollHeight;
            }
        </script>
    </body>
    </html>
    """


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for user questions."""
    try:
        result = await query_assistant(request.message)
        return ChatResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )