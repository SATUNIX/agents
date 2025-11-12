# Architecture Overview

## Runtime Layers

1. **Entrypoint (`python -m agent`)**
   - Typer CLI exposes run/resume, config inspection, policy/MCP utilities, and the observability dashboard.
2. **Runtime Wiring (`agent.runtime.AgentRuntime`)**
   - Loads `AgentConfig`, policies, telemetry, builds the SDK `Agent` (function tools + Hosted MCP), and hands it to an `openai.agents.Runner`.
3. **Reasoning Loop (`openai.agents.Agent` + `Runner`)**
   - The SDK handles planning/execution internally; upcoming Epics will add `@function_tool` hooks for filesystem + MPC actions.
4. **Tooling Layer (`agent.function_tools`)**
   - Local deterministic tools are registered via `@function_tool` decorators (read/write/shell/repo summary) and emit telemetry directly; remote tools are declared via `HostedMCPTool`.
5. **State & Telemetry (`agent.state.StateManager`)**
   - JSONL audit logs and metrics (`metrics.json`) plus release artifacts (`/state/release_artifacts`). SDK persistence handles checkpoints internally.
6. **Observability (`agent.observability.dashboard`)**
   - FastAPI service on port 7081 exposes health, metrics, logs, checkpoints, and MCP endpoint data (including `/mcp` + `/mcp/health` cards).
7. **Policy-as-Code (`policies/*.yaml` + `agent.policies.PolicyManager`)**
   - Central policy bundle, hot-reloadable via SIGHUP or REST, enforces command allowlists, network posture, path constraints, and token/tool budgets.

## Data Directories

| Path | Purpose |
| --- | --- |
| `/workspace` | User repository for read/write operations. |
| `/state` | Logs, checkpoints, metrics, release artifacts, dashboard snapshots. |
| `/tools` | Installed local tools and caches. |
| `/state/tools/mcp_endpoints.json` | MCP health snapshot. |
| `/state/agent.pid` | PID reference for policy reloads. |
| `policies/` | Policy-as-code bundle (mounted via `AGENT_POLICY_DIR`). |

## Networking

- LM Studio endpoint: `http://host.docker.internal:1234/v1` (configurable via `OPENAI_BASE_URL`). Use `AGENT_FORCE_CHAT_COMPLETIONS=true` to force chat-only fallback for LM Studio.
- Docker Compose exposes the main agent and optional dashboard container; `ALLOW_NET` and policy YAML control outbound calls.
- MCP endpoints defined in `config/settings.yaml` specify transport (`http`, `ws`, etc.), rate limits, and secrets.

## Security Controls

- Guardrails enforce workspace path normalization, command allowlists (supporting multi-word commands and env overrides), and network gating sourced from policy YAML.
- Reviewer prompt includes policy reminders from `config/settings.yaml`.
- Container runs as non-root user with `tini` and health checks.
