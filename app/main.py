"""FastAPI application for RAG-L1-Support-Bot."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

from app.rag import query_assistant, check_assistant_status
from app.routes.stream import chat_router

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

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(chat_router)


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


@app.get("/")
async def root(request: Request):
    """Web interface for chatting with the assistant."""
    return templates.TemplateResponse("index.html", {"request": request})


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