# OpenAI Agent SDK Design Specification

## Overview

This specification defines a **Docker-deployed OpenAI Agent** built using the **OpenAI Agents SDK**. The agent operates within a **containerized, isolated environment** with full read/write access to a **bind-mounted workspace**, LAN connectivity, hosted tool downloads, and multi-turn planning/thinking capabilities. The agent connects to an **LM Studio endpoint** running on the host machine for LLM completions.

---

## 1. Objectives

* Provide controlled read/write access within an allocated workspace (bind mount).
* Operate autonomously through multi-turn planning, reasoning, and execution loops.
* Use LM Studio (OpenAI-compatible endpoint) for all LLM interactions.
* Support tool installation and updates inside the container environment.
* Enable LAN and optional internet access for local service calls.
* Maintain state persistence, checkpointing, and logging for long-running sessions.

---

## 2. High-Level Architecture

**Process:** `agent.py` (main entrypoint)

**LLM Provider:** LM Studio OpenAI-compatible endpoint hosted on the Docker host.

**Tools:**

* **Hosted MCP tools:** Connected via remote URLs for API, web, or data access (declared via `HostedMCPTool`).
* **Local tools:** Implemented as SDK `@function_tool` callables with workspace guardrails.

**Storage:**

* `/workspace` → Bound project directory for read/write access.
* `/state` → Internal agent state (logs, checkpoints, cache).
* `/tools` → Local tool installations.

**Networking:**

* LAN access via Docker `bridge` or `host.docker.internal` mapping.
* LM Studio accessible at `http://host.docker.internal:1234/v1`.

---

## 3. Container Configuration

### Dockerfile

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates build-essential tini && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 agent
WORKDIR /app
RUN mkdir -p /workspace /state /tools && chown -R agent:agent /workspace /state /tools /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN chown -R agent:agent /app
USER agent

ENV PYTHONUNBUFFERED=1 \
    AGENT_WORKSPACE=/workspace \
    AGENT_STATE_DIR=/state \
    AGENT_TOOLS_DIR=/tools \
    OPENAI_API_KEY="sk-fake" \
    OPENAI_BASE_URL="http://host.docker.internal:1234/v1" \
    AGENT_MODEL="gpt-4o-mini"

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "agent"]
```

### docker-compose.yaml

```yaml
version: "3.9"
services:
  dev-agent:
    build: .
    image: agent:dev
    container_name: dev-agent
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      OPENAI_API_KEY: "sk-fake"
      OPENAI_BASE_URL: "http://host.docker.internal:1234/v1"
      AGENT_MODEL: "gpt-4o-mini"
      AGENT_WORKSPACE: /workspace
      AGENT_STATE_DIR: /state
      AGENT_TOOLS_DIR: /tools
      ALLOW_NET: "true"
    volumes:
      - ./projects/demo:/workspace
      - agent_state:/state
    ports:
      - "7081:7081/tcp"
    restart: unless-stopped
volumes:
  agent_state:
```

---

## 4. Environment Variables

| Variable          | Description                                 |
| ----------------- | ------------------------------------------- |
| `OPENAI_BASE_URL` | LM Studio API endpoint.                     |
| `OPENAI_API_KEY`  | Placeholder API key (LM Studio ignores it). |
| `AGENT_MODEL`     | Default LLM model alias.                    |
| `AGENT_WORKSPACE` | Path to the mounted project directory.      |
| `AGENT_STATE_DIR` | Persistent agent logs and checkpoints.      |
| `AGENT_TOOLS_DIR` | Directory for downloaded/installed tools.   |
| `ALLOW_NET`       | Controls outbound network access.           |

---

## 5. Agent Composition

### Agent Roles

1. **Planner** → Decomposes user goal into actionable steps.
2. **Executor** → Executes steps with tool calls and environment access.
3. **Reviewer** → Validates outcomes and determines next steps.

### Tooling System

* **Hosted MCP Tools:** Remote MCP endpoints for API/data integration (declared via `HostedMCPTool`).
* **Local Tools:** SDK `@function_tool` callables executed within the workspace guardrails.

### State and Persistence

* State files stored in `/state/run-<id>.jsonl`.
* Checkpoints every N tool calls for recovery.
* Logs tool invocations, environment actions, and errors.

---

## 6. Planning and Execution Loop

**Flow:**

1. Receive goal input.
2. Generate structured plan (task tree or DAG).
3. Execute plan iteratively using ReACT-style reasoning:

   * Thought → Action (tool call) → Observation → Next Thought.
4. Save results, audit logs, and checkpoints.
5. Terminate when all steps validated or goal reached.

**Resumability:**

* On restart, agent loads last checkpoint and resumes remaining steps.

---

## 7. Security & Guardrails

* **Path normalization** ensures all reads/writes remain inside `/workspace`.
* **Command allowlist** for subprocesses, limited runtime and memory.
* **Network policy** disables outbound traffic unless explicitly enabled.
* **Tool provenance logging** for versioning and reproducibility.
* **Audit trail** with timestamped JSONL logs stored in `/state/audit/`.

---

## 8. Example Runtime Flow

```bash
# Start LM Studio on host
lmstudio server --port 1234

# Start container
docker compose up -d

# Execute agent goal
docker exec -it dev-agent python -m agent "Refactor source code and write changelog"
```

**Agent Behavior:**

* Reads `/workspace` files.
* Plans refactor tasks.
* Uses LM Studio for reasoning.
* Writes updated files to `/workspace`.
* Saves progress to `/state`.

---

## 9. Future Extensions

* **Multi-agent hierarchy:** Planner/Worker/Reviewer split across isolated agents.
* **Observability hooks:** Stream telemetry to OpenTelemetry or ELK.
* **Policy Engine:** YAML-based fine-grained permissions for file/tool access.
* **Guardrails integration:** Pre-checks for code commits, tests, or CI tasks.

---

## 10. Policy-as-Code & Tool Enforcement

* Policies live under `policies/{tools.yaml,network.yaml,paths.yaml}` and are loaded via `PolicyManager` with budgets for tool calls/tokens.
* Guardrails consume both YAML and `config/settings.yaml` globs; multi-word command allowlists and env overrides (`AGENT_ALLOWED_COMMANDS`) are supported.
* Operators can validate or reload policies at runtime via `python -m agent policies validate` / `policies reload` (SIGHUP) or the dashboard `POST /policies/reload` endpoint.
* Local actions are exposed to the SDK via `@function_tool` (see `src/agent/function_tools.py`), ensuring guardrails and telemetry live inside each tool definition.

---

## 11. MCP Connectivity & Health

* `MCPClientManager` supports HTTP, WebSocket, and STDIO transports with auth tokens, rate limiting, and audit telemetry (`mcp_invoke` events).
* CLI: `python -m agent mcp health`; tool invocations occur through normal goals using `HostedMCPTool` definitions.
* Dashboard exposes `/mcp` + `/mcp/health` cards summarizing latency, throttling, and total invocations; release snapshots stored under `/state/tools/mcp_endpoints.json`.

---

## 12. Compatibility & Release Readiness

* Responses vs chat fallback is auto-detected but can be forced via `AGENT_FORCE_CHAT_COMPLETIONS=true`; `scripts/smoke_test.py` exercises both modes (CI + nightly chaos workflow).
* Documentation portal (`docs/`) contains architecture, guides (including tool execution demo), runbooks (policy/network troubleshooting), and reports (compatibility matrix, GA readiness, gap analysis).
* Release checklist references SBOM/Trivy/Cosign outputs plus newly required evidence (SDK snapshot, MCP health dump, chaos log) before tagging GA builds.

---

## 10. References

* OpenAI Agents SDK (Python): Loops, tools, guardrails, handoffs.
* Model Context Protocol (MCP): Hosted tool discovery/invocation.
* LM Studio Documentation: OpenAI-compatible `/v1` endpoint.
* Docker networking: host-gateway mapping for local service access.

---

## 11. Summary

This design delivers a **self-contained development and reasoning agent** capable of performing long-running, autonomous operations inside an isolated Docker environment. It balances autonomy, stability, and security—ideal for development workflows, automated documentation, and code operations managed through a controlled LM Studio-based backend.
