# Runbook

## High Error Rate

1. Check `LLMGatewayHighErrorRate` labels and recent deploys.
2. Compare `status="backend_unavailable"` with backend pod restarts.
3. Inspect gateway logs by request ID.
4. Roll back the gateway image or backend model revision if errors correlate with deploy time.

## High Latency

1. Check p95 latency by model in Grafana.
2. Compare prompt and completion token throughput with request rate.
3. Inspect backend queue depth and GPU utilization.
4. Increase replicas, reduce max tokens, or enable continuous batching depending on the bottleneck.

## Backend Migration

1. Deploy new backend behind a separate Service.
2. Set `LLM_BACKEND_URL` in a canary overlay.
3. Compare metrics for latency, error rate, and token throughput.
4. Promote only after canary traffic is stable.
