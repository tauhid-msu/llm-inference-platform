import time
import uuid
from abc import ABC, abstractmethod

import httpx

from .config import Settings
from .schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    TokenUsage,
)


class InferenceBackend(ABC):
    @abstractmethod
    async def complete(self, request: ChatCompletionRequest, model: str) -> ChatCompletionResponse:
        """Return a chat completion response for the requested model."""
        raise NotImplementedError


def estimate_tokens(text: str) -> int:
    """Estimate token count with a lightweight whitespace-based approximation."""
    return max(1, len(text.split()))


def estimate_prompt_tokens(request: ChatCompletionRequest) -> int:
    """Estimate total prompt tokens across all messages in a chat request."""
    return sum(estimate_tokens(message.content) for message in request.messages)


class MockBackend(InferenceBackend):
    async def complete(self, request: ChatCompletionRequest, model: str) -> ChatCompletionResponse:
        """Generate a deterministic local response without calling an external model server."""
        prompt_tokens = estimate_prompt_tokens(request)
        last_user = next(
            (message.content for message in reversed(request.messages) if message.role == "user"),
            request.messages[-1].content,
        )
        content = (
            "Mock inference response: "
            f"received {prompt_tokens} prompt tokens for model '{model}'. "
            f"Last user message was: {last_user[:160]}"
        )
        completion_tokens = estimate_tokens(content)
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )


class OpenAICompatibleBackend(InferenceBackend):
    def __init__(self, settings: Settings) -> None:
        """Store backend connection settings for later inference calls."""
        self.settings = settings

    async def complete(self, request: ChatCompletionRequest, model: str) -> ChatCompletionResponse:
        """Forward the chat completion request to an OpenAI-compatible backend."""
        payload = request.model_dump()
        payload["model"] = model
        async with httpx.AsyncClient(timeout=self.settings.backend_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.backend_url.rstrip('/')}/v1/chat/completions",
                json=payload,
            )
            response.raise_for_status()
        return ChatCompletionResponse.model_validate(response.json())


def build_backend(settings: Settings) -> InferenceBackend:
    """Create the configured inference backend implementation."""
    if settings.backend_kind == "openai_compatible":
        return OpenAICompatibleBackend(settings)
    return MockBackend()
