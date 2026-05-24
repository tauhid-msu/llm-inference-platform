# Resume Notes

## Project Title

Production-grade LLM inference and observability platform on Kubernetes

## Resume Bullets

- Built an OpenAI-compatible LLM inference gateway in FastAPI with backend adapters for mock, vLLM, and TGI-style model servers.
- Designed Kubernetes deployment assets with probes, resource controls, HPA, PodDisruptionBudget, NetworkPolicy, and Kustomize overlays.
- Implemented Prometheus metrics, Grafana dashboards, and alert rules for request rate, p95 latency, token throughput, and backend error rate.
- Added OpenTelemetry instrumentation to correlate API requests with downstream model-serving calls.
- Created load testing and smoke testing workflows to validate reliability and performance before deployment.

## Interview Talking Points

- Explain why gateway and model backend scaling should be decoupled.
- Discuss p95/p99 latency, token throughput, queue depth, and GPU utilization as separate signals.
- Describe rollout strategy for new model versions using canaries and metric comparison.
- Show how prompt limits, request IDs, readiness checks, and alerts reduce operational risk.
