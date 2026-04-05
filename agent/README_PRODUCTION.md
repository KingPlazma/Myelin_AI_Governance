# Myelin Sentinel Production Notes

This agent is a middleware service that sits between your chatbot application and a downstream LLM.

## Architecture

- `proxy_server.py`: FastAPI ingress and operational endpoints
- `service.py`: orchestration flow for prompt audit, downstream call, response audit, and remediation
- `provider_client.py`: downstream LLM adapter
- `incident_store.py`: durable SQLite incident logging
- `alerting.py`: optional backend-auth and notification integration
- `config.py`: environment-driven service configuration
- `metrics.py`: in-process operational counters
- `operational_auth.py`: token gate for ops endpoints

## Endpoints

- `GET /`
- `GET /health`
- `GET /ready`
- `GET /incidents/recent`
- `GET /metrics`
- `POST /v1/chat/completions`

## Production behavior in this version

- prompt pre-audit with optional blocking
- downstream forwarding with explicit error propagation
- response post-audit and remediation
- incident logging to `MYELIN_INCIDENT_DB_PATH`
- readiness based on downstream LLM reachability
- env-driven runtime configuration
- protected operational endpoints using `X-Myelin-Ops-Token`
- provider support for OpenAI-compatible endpoints, Ollama, and Anthropic-style chat APIs

## Run

```bash
cd agent
python run_agent.py
```

## Git-based deployment path

Use Git for source distribution and a process manager for runtime:

1. clone or pull the repo on the target server
2. create a Python virtual environment
3. install requirements from the repo
4. set `agent/.env`
5. run the service with `systemd`, `supervisord`, or another process manager

The repo can be deployed without Docker.

## Deploy next

- put behind a process manager such as `systemd`, `supervisord`, or container orchestration
- ship incident logs to a real datastore
- add metrics and tracing
- add auth on operational endpoints
- add provider adapters for OpenAI, Anthropic, Azure OpenAI, and internal gateways
