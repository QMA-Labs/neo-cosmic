from contextlib import contextmanager
from threading import Event

import httpx
import pytest

from neo.core.ollama_client import ChatCancelled, OllamaClient


def test_status_is_graceful_when_offline(monkeypatch) -> None:
    def offline(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "get", offline)
    status = OllamaClient("http://localhost:11434").status()
    assert status.reachable is False
    assert status.error


def test_status_lists_models(monkeypatch) -> None:
    request = httpx.Request("GET", "http://localhost/api/tags")
    response = httpx.Response(200, request=request, json={"models": [{"name": "qwen3.5:9b"}]})
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)
    status = OllamaClient("http://localhost").status()
    assert status.models == ("qwen3.5:9b",)


def test_streaming_chat_can_be_cancelled(monkeypatch) -> None:
    request = httpx.Request("POST", "http://localhost/api/chat")
    response = httpx.Response(
        200,
        request=request,
        content=b'{"message":{"content":"first"}}\n',
    )
    @contextmanager
    def fake_stream(*args, **kwargs):
        yield response

    monkeypatch.setattr(httpx, "stream", fake_stream)
    cancelled = Event()
    cancelled.set()
    with pytest.raises(ChatCancelled):
        OllamaClient("http://localhost").chat("model", "hello", cancel_event=cancelled)


def test_streaming_chat_never_exposes_thinking_when_content_is_empty(monkeypatch) -> None:
    request = httpx.Request("POST", "http://localhost/api/chat")
    response = httpx.Response(
        200,
        request=request,
        content=b'{"message":{"content":"","thinking":"fallback answer"}}\n',
    )

    @contextmanager
    def fake_stream(*args, **kwargs):
        yield response

    monkeypatch.setattr(httpx, "stream", fake_stream)
    assert OllamaClient("http://localhost").chat("model", "hello") == ""
