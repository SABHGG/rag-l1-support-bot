"""Tests for RAG module."""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_assistant_client():
    with patch("app.rag.AssistantClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.mark.asyncio
async def test_query_assistant_returns_proper_structure(mock_assistant_client):
    from app.rag import query_assistant

    mock_assistant_client.chat.return_value = {
        "message": {
            "content": "Test answer about password reset."
        },
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        },
        "citations": []
    }

    result = await query_assistant("How do I reset password?")

    assert "answer" in result
    assert "sources" in result
    assert "finish_reason" in result
    assert "usage" in result
    assert result["finish_reason"] == "stop"
    assert result["usage"]["total_tokens"] == 150


@pytest.mark.asyncio
async def test_query_assistant_extracts_citations(mock_assistant_client):
    from app.rag import query_assistant

    mock_assistant_client.chat.return_value = {
        "message": {
            "content": "According to the manual..."
        },
        "finish_reason": "stop",
        "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75},
        "citations": [
            {
                "references": [
                    {
                        "pages": [1, 2],
                        "file": {
                            "name": "test-manual.pdf",
                            "metadata": {"category": "test"}
                        }
                    }
                ]
            }
        ]
    }

    result = await query_assistant("Test question")

    assert len(result["sources"]) == 1
    assert result["sources"][0]["name"] == "test-manual.pdf"
    assert result["sources"][0]["pages"] == [1, 2]


@pytest.mark.asyncio
async def test_check_assistant_status_ready(mock_assistant_client):
    from app.rag import check_assistant_status

    mock_assistant_client.chat.return_value = {"message": {"content": "ok"}}

    status = await check_assistant_status()

    assert status["status"] == "ok"
    assert status["assistant"] == "ready"


@pytest.mark.asyncio
async def test_check_assistant_status_error(mock_assistant_client):
    from app.rag import check_assistant_status

    mock_assistant_client.chat.side_effect = Exception("API Error")

    status = await check_assistant_status()

    assert status["status"] == "error"
    assert status["assistant"] == "error"