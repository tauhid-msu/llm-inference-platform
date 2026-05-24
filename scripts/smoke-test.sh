#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

curl -fsS "${BASE_URL}/healthz" >/dev/null
curl -fsS "${BASE_URL}/readyz" >/dev/null
curl -fsS "${BASE_URL}/v1/chat/completions" \
  -H 'content-type: application/json' \
  -d '{"model":"resume-llm","messages":[{"role":"user","content":"Say hello from the smoke test."}]}' \
  | python3 -m json.tool
