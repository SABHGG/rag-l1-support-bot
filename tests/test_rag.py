"""Tests for RAG module."""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_assistant_client():
    with patch("app.rag.AssistantClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_chat_response():
    """Mock ChatResponse-like object."""
    response = MagicMock()
    response.message = MagicMock()
    response.message.content = "Test answer about password reset."
    response.finish_reason = "stop"
    response.usage = MagicMock()
    response.usage.prompt_tokens = 100
    response.usage.completion_tokens = 50
    response.usage.total_tokens = 150
    response.citations = []
    return response


@pytest.fixture
def mock_chat_response_with_citations():
    """Mock ChatResponse with citations."""
    response = MagicMock()
    response.message = MagicMock()
    response.message.content = "According to the manual..."
    response.finish_reason = "stop"
    response.usage = MagicMock()
    response.usage.prompt_tokens = 50
    response.usage.completion_tokens = 25
    response.usage.total_tokens = 75

    file_model = MagicMock()
    file_model.name = "test-manual.pdf"
    file_model.metadata = {"category": "test"}

    ref = MagicMock()
    ref.file = file_model
    ref.pages = [1, 2]

    cit = MagicMock()
    cit.references = [ref]

    response.citations = [cit]
    return response


@pytest.mark.asyncio
async def test_query_assistant_returns_proper_structure(mock_assistant_client, mock_chat_response):
    from app.rag import query_assistant

    mock_assistant_client.chat.return_value = mock_chat_response

    result = await query_assistant("How do I reset password?")

    assert "answer" in result
    assert "sources" in result
    assert "finish_reason" in result
    assert "usage" in result
    assert result["finish_reason"] == "stop"
    assert result["usage"]["total_tokens"] == 150


@pytest.mark.asyncio
async def test_query_assistant_extracts_citations(mock_assistant_client, mock_chat_response_with_citations):
    from app.rag import query_assistant

    mock_assistant_client.chat.return_value = mock_chat_response_with_citations

    result = await query_assistant("Test question")

    assert len(result["sources"]) == 1
    assert result["sources"][0]["name"] == "test-manual.pdf"
    assert result["sources"][0]["pages"] == [1, 2]


@pytest.mark.asyncio
async def test_check_assistant_status_ready(mock_assistant_client):
    from app.rag import check_assistant_status

    mock_assistant_client.chat.return_value = MagicMock()

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