# Architecture

The platform separates client-facing API stability from model-serving implementation details.

## Components

- **Inference gateway**: validates OpenAI-compatible chat requests, applies prompt budget checks, forwards to a backend, and emits metrics/traces.
- **Backend adapter**: supports local mock responses for development and OpenAI-compatible HTTP backends for vLLM or Hugging Face TGI deployments.
- **Kubernetes control plane**: Deployment, Service, HPA, PDB, probes, NetworkPolicy, and environment-specific Kustomize overlays.
- **Observability**: Prometheus metrics, Grafana dashboard, alert rules, and OTLP trace export hooks.

## Production Notes

- Use dedicated GPU node pools and topology spread constraints for real model servers.
- Scale the gateway on CPU/request rate and scale model backends on GPU utilization, queue depth, and time-to-first-token.
- Add request authentication at ingress or API gateway boundaries.
- Store model artifacts in object storage or a model registry, then preload with init containers or node-local caches.
- Add canary routing before model upgrades to compare latency and answer quality.
