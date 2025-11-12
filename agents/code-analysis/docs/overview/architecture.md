# Architecture Overview

## Runtime Layers

1. **Entrypoint (`python -m agent`)**
   - Typer CLI exposes run/resume, config inspection, tool invocation, checkpoint ops, and the observability dashboard.
2. **Runtime Wiring (`agent.runtime.AgentRuntime`)**
   - Loads `AgentConfig` (Pydantic + YAML registry + secrets), instantiates `StateManager`, LLM client, tool registry/invoker, MCP manager, and orchestrator.
3. **Reasoning Loop (`agent.loop.AgentOrchestrator`)**
   - Planner → Executor → Reviewer roles implemented via the OpenAI Agents SDK (with chat-completion fallback) share an `AgentSession` checkpoint across runs.
4. **Tooling Layer (`agent.tools.*`)**
   - Local deterministic tools (read/write/shell/repo summary) include schemas, guardrails, auditing, and metrics hooks; remote tools are declared via MPC endpoints.
5. **State & Telemetry (`agent.state.StateManager`)**
   - JSONL audit logs, metrics (`metrics.json`), checkpoints (`/state/checkpoints/<run-id>`), and release artifacts (`/state/release_artifacts`).
6. **Observability (`agent.observability.dashboard`)**
   - FastAPI service on port 7081 exposes health, metrics, logs, checkpoints, and MCP endpoint data.

## Data Directories

| Path | Purpose |
| --- | --- |
| `/workspace` | User repository for read/write operations. |
| `/state` | Logs, checkpoints, metrics, release artifacts, dashboard snapshots. |
| `/tools` | Installed local tools and caches. |
| `/state/tools/registry.json` | Tool manifest for reproducibility. |
| `/state/tools/mcp_endpoints.json` | MCP health snapshot. |

## Networking

- LM Studio endpoint: `http://host.docker.internal:1234/v1` (configurable via `OPENAI_BASE_URL`).
- Docker Compose exposes the main agent and optional dashboard container; `ALLOW_NET` toggles network tool behavior.
- MCP endpoints defined in `config/settings.yaml` specify transport (`http`, `ws`, etc.), rate limits, and secrets.

## Security Controls

- Guardrails enforce workspace path normalization, command allowlists, and network gating.
- Reviewer prompt includes policy reminders from `config/settings.yaml`.
- Container runs as non-root user with `tini` and health checks.
