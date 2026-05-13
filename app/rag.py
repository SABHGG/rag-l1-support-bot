"""RAG logic for querying the assistant."""

from typing import List

from sync.assistant_client import AssistantClient


async def query_assistant(message: str) -> dict:
    """Query Pinecone Assistant and format response."""
    client = AssistantClient()
    response = client.chat(message)

    msg = response.message
    answer = msg.content if hasattr(msg, 'content') else msg.get('content', '')

    citations = _extract_citations(response)
    usage = response.usage

    return {
        "answer": answer,
        "sources": citations,
        "finish_reason": response.finish_reason,
        "usage": {
            "prompt_tokens": usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else 0,
            "completion_tokens": usage.completion_tokens if hasattr(usage, 'completion_tokens') else 0,
            "total_tokens": usage.total_tokens if hasattr(usage, 'total_tokens') else 0
        }
    }


def _extract_citations(response) -> List[dict]:
    """Extract sources from Pinecone Assistant citations."""
    citations = []
    for cit in response.citations:
        for ref in cit.references:
            file_info = ref.file
            citations.append({
                "name": file_info.name if hasattr(file_info, 'name') else file_info.get('name', 'unknown'),
                "pages": ref.pages if ref.pages else [],
                "metadata": file_info.metadata if hasattr(file_info, 'metadata') else {}
            })
    return citations


async def check_assistant_status() -> dict:
    """Check if Pinecone Assistant is ready."""
    try:
        client = AssistantClient()
        client.chat("test")
        return {"status": "ok", "assistant": "ready"}
    except Exception as e:
        return {"status": "error", "assistant": "error", "message": str(e)}