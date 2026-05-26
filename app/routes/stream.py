"""SSE streaming endpoint for chat."""

import json
from typing import AsyncGenerator, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from sync.assistant_client import AssistantClient

chat_router = APIRouter()


class ChatStreamRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    model: str = "gpt-4o"


def _sse(event_type: str, **data) -> str:
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload)}\n\n"


def _stream_generator(request: ChatStreamRequest) -> AsyncGenerator[str, None]:
    client = AssistantClient()
    sources: list = []
    try:
        for chunk in client.chat_stream(
            request.message,
            model=request.model,
            thread_id=request.thread_id,
        ):
            # Pinecone SDK streams MessageChunk objects with a .content attribute
            # and may also yield citation data in the final chunk
            content = None
            if hasattr(chunk, "content"):
                content = chunk.content
            elif isinstance(chunk, dict):
                content = chunk.get("content")

            if content:
                yield _sse("token", content=content)

            # Citations may appear in the chunk as .citations attribute
            if hasattr(chunk, "citations") and chunk.citations:
                for cit in chunk.citations:
                    if not hasattr(cit, "references"):
                        continue
                    for ref in cit.references:
                        file_info = ref.file
                        sources.append({
                            "name": file_info.name if hasattr(file_info, "name") else file_info.get("name", "unknown"),
                            "pages": ref.pages if ref.pages else [],
                            "metadata": file_info.metadata if hasattr(file_info, "metadata") else {},
                        })

        yield _sse("sources", sources=sources)
        yield _sse("done")
    except Exception as exc:
        yield _sse("error", message=str(exc))


@chat_router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest) -> StreamingResponse:
    """Stream chat response as Server-Sent Events."""
    return StreamingResponse(
        _stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
