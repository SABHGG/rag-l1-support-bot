"""Tests for SSE streaming endpoint."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_chunk(content: str) -> MagicMock:
    chunk = MagicMock()
    chunk.content = content
    chunk.citations = []
    return chunk


@pytest.fixture
def stream_client():
    from fastapi import FastAPI
    from app.routes.stream import chat_router

    app = FastAPI()
    app.include_router(chat_router)
    return TestClient(app)


def test_stream_emits_token_and_done_events(stream_client):
    chunks = [_make_chunk("Hello"), _make_chunk(" world"), _make_chunk("!")]

    with patch("app.routes.stream.AssistantClient") as MockClient:
        MockClient.return_value.chat_stream.return_value = iter(chunks)

        resp = stream_client.post("/chat/stream", json={"message": "hi"})

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    lines = [line for line in resp.text.split("\n\n") if line.startswith("data:")]
    events = [json.loads(line[len("data: "):]) for line in lines]

    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) == 3
    assert token_events[0]["content"] == "Hello"
    assert token_events[1]["content"] == " world"
    assert token_events[2]["content"] == "!"

    sources_events = [e for e in events if e["type"] == "sources"]
    assert len(sources_events) == 1
    assert sources_events[0]["sources"] == []

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1


def test_stream_emits_error_on_exception(stream_client):
    with patch("app.routes.stream.AssistantClient") as MockClient:
        MockClient.return_value.chat_stream.side_effect = RuntimeError("SDK failure")

        resp = stream_client.post("/chat/stream", json={"message": "fail"})

    assert resp.status_code == 200
    lines = [line for line in resp.text.split("\n\n") if line.startswith("data:")]
    events = [json.loads(line[len("data: "):]) for line in lines]

    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 1
    assert "SDK failure" in error_events[0]["message"]


def test_stream_forwards_thread_id(stream_client):
    chunks = [_make_chunk("ok")]

    with patch("app.routes.stream.AssistantClient") as MockClient:
        instance = MockClient.return_value
        instance.chat_stream.return_value = iter(chunks)

        stream_client.post("/chat/stream", json={"message": "test", "thread_id": "abc-123"})

        instance.chat_stream.assert_called_once_with(
            "test", model="gpt-4o", thread_id="abc-123"
        )
