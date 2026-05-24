from app.main import app
from fastapi.testclient import TestClient


def test_healthz() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_completion_mock_backend() -> None:
    payload = {
        "model": "resume-llm",
        "messages": [{"role": "user", "content": "What is continuous batching?"}],
    }
    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)
    body = response.json()
    assert response.status_code == 200
    assert body["object"] == "chat.completion"
    assert body["model"] == "resume-llm"
    assert body["usage"]["total_tokens"] >= body["usage"]["prompt_tokens"]
    assert "Mock inference response" in body["choices"][0]["message"]["content"]


def test_rejects_oversized_prompt(monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_MAX_PROMPT_CHARS", "10")
    payload = {
        "messages": [{"role": "user", "content": "this prompt is too long for the test budget"}],
    }
    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)
    get_settings.cache_clear()
    assert response.status_code == 413
