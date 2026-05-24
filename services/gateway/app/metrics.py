from prometheus_client import Counter, Histogram

REQUESTS = Counter(
    "llm_gateway_requests_total",
    "Total chat completion requests.",
    ["model", "status"],
)

LATENCY = Histogram(
    "llm_gateway_request_duration_seconds",
    "End-to-end gateway request latency.",
    ["model"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

TOKENS = Counter(
    "llm_gateway_tokens_total",
    "Total estimated prompt and completion tokens.",
    ["model", "type"],
)

BACKEND_ERRORS = Counter(
    "llm_gateway_backend_errors_total",
    "Total backend inference errors.",
    ["model", "backend_kind"],
)
