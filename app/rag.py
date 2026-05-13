"""RAG logic for querying the assistant."""

from typing import List, Optional

from sync.assistant_client import AssistantClient


async def query_assistant(message: str) -> dict:
    """Query Pinecone Assistant and format response."""
    client = AssistantClient()
    response = client.chat(message)

    answer = response.get("message", {}).get("content", "")
    citations = _extract_citations(response)
    usage = response.get("usage", {})

    return {
        "answer": answer,
        "sources": citations,
        "finish_reason": response.get("finish_reason", "stop"),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
    }


def _extract_citations(response: dict) -> List[dict]:
    """Extract sources from Pinecone Assistant citations."""
    citations = []
    for ref in response.get("citations", []):
        for ref_data in ref.get("references", []):
            file_info = ref_data.get("file", {})
            citations.append({
                "name": file_info.get("name", "unknown"),
                "pages": ref_data.get("pages", []),
                "metadata": file_info.get("metadata", {})
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