import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .backend import build_backend
from .config import get_settings
from .metrics import BACKEND_ERRORS, LATENCY, REQUESTS, TOKENS
from .schemas import ChatCompletionRequest, ChatCompletionResponse
from .telemetry import configure_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared settings and the inference backend for the app lifecycle."""
    settings = get_settings()
    app.state.settings = settings
    app.state.backend = build_backend(settings)
    yield


app = FastAPI(
    title="LLM Inference Gateway",
    version="0.1.0",
    description="OpenAI-compatible LLM inference gateway with production observability.",
    lifespan=lifespan,
)
configure_telemetry(app, get_settings())


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Attach a request ID to every response so logs, traces, and clients can correlate work."""
    request_id = request.headers.get("x-request-id", f"req-{time.time_ns()}")
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Report whether the gateway process is alive."""
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(request: Request) -> dict[str, str]:
    """Report whether the gateway is ready to receive inference traffic."""
    settings = request.app.state.settings
    if settings.backend_kind == "mock":
        return {"status": "ready", "backend": "mock"}
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.get(f"{settings.backend_url.rstrip('/')}/healthz")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="backend unavailable") from exc
    return {"status": "ready", "backend": settings.backend_kind}


@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics for scraping."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request_body: ChatCompletionRequest,
    request: Request,
) -> ChatCompletionResponse:
    """Validate and execute an OpenAI-compatible chat completion request."""
    settings = request.app.state.settings
    model = request_body.model or settings.default_model
    prompt_chars = sum(len(message.content) for message in request_body.messages)
    if prompt_chars > settings.max_prompt_chars:
        REQUESTS.labels(model=model, status="rejected").inc()
        raise HTTPException(status_code=413, detail="prompt exceeds configured character budget")

    start = time.perf_counter()
    try:
        response = await request.app.state.backend.complete(request_body, model)
    except httpx.HTTPStatusError as exc:
        BACKEND_ERRORS.labels(model=model, backend_kind=settings.backend_kind).inc()
        REQUESTS.labels(model=model, status="backend_error").inc()
        raise HTTPException(status_code=502, detail="backend inference request failed") from exc
    except httpx.HTTPError as exc:
        BACKEND_ERRORS.labels(model=model, backend_kind=settings.backend_kind).inc()
        REQUESTS.labels(model=model, status="backend_unavailable").inc()
        raise HTTPException(status_code=503, detail="backend unavailable") from exc
    finally:
        LATENCY.labels(model=model).observe(time.perf_counter() - start)

    REQUESTS.labels(model=model, status="ok").inc()
    TOKENS.labels(model=model, type="prompt").inc(response.usage.prompt_tokens)
    TOKENS.labels(model=model, type="completion").inc(response.usage.completion_tokens)
    return response
