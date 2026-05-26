from app.backend import OllamaBackend
from app.config import Settings
from app.main import app
from app.schemas import ChatCompletionRequest
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


async def test_ollama_backend_maps_response(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "message": {"role": "assistant", "content": "Real local model response."},
                "done": True,
                "prompt_eval_count": 7,
                "eval_count": 4,
            }

    class FakeAsyncClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, url: str, json: dict) -> FakeResponse:
            assert url == "http://ollama.local/api/chat"
            assert json["model"] == "llama3.2"
            assert json["stream"] is False
            assert json["messages"] == [{"role": "user", "content": "Hello"}]
            return FakeResponse()

    monkeypatch.setattr("app.backend.httpx.AsyncClient", FakeAsyncClient)
    backend = OllamaBackend(
        Settings(
            backend_kind="ollama",
            backend_url="http://ollama.local",
            default_model="llama3.2",
        )
    )
    response = await backend.complete(
        ChatCompletionRequest(messages=[{"role": "user", "content": "Hello"}]),
        "llama3.2",
    )
    assert response.model == "llama3.2"
    assert response.choices[0].message.content == "Real local model response."
    assert response.usage.total_tokens == 11
