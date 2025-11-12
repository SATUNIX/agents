# OpenAI Agent SDK Implementation Notes

## Purpose

This document distills the responsibilities and runtime expectations for the Docker-deployed OpenAI Agent described in `SpecSheet.md`. Use it as an onboarding reference when extending, testing, or operating the project.

## Core Guarantees

- **Execution Model:** `python -m agent` launches an autonomous loop (Planner → Executor → Reviewer) that iteratively reasons, calls tools, and validates progress.
- **LLM Backend:** All model calls route through the LM Studio OpenAI-compatible endpoint at `http://host.docker.internal:1234/v1` using the `gpt-4o-mini` alias by default.
- **Storage Layout:**
  - `/workspace` contains the bind-mounted project files that the agent may read/write.
  - `/state` stores audit logs, checkpoints (`run-<id>.jsonl`), and resumable metadata.
  - `/tools` holds downloaded/installed tool bundles managed by the agent.
- **Networking:** The container can reach LAN resources (and optionally the wider internet) via Docker `bridge` networking plus `host.docker.internal` mapping.
- **Security:** Path normalization confines filesystem actions to `/workspace`; subprocesses follow a curated allowlist; every tool invocation and network action is logged for provenance.

## Runtime Configuration

| Variable | Purpose |
| --- | --- |
| `OPENAI_BASE_URL` | LM Studio endpoint URL. |
| `OPENAI_API_KEY` | Placeholder key (LM Studio ignores it but clients require a token). |
| `AGENT_MODEL` | Default completion model (e.g., `gpt-4o-mini`). |
| `AGENT_WORKSPACE` | Absolute path to the mounted project directory. |
| `AGENT_STATE_DIR` | Directory for logs, checkpoints, audit trails. |
| `AGENT_TOOLS_DIR` | Root path for installing local tools. |
| `ALLOW_NET` | String flag that toggles outbound networking. |

The Docker image creates a non-root `agent` user (UID 1000) and sets sane defaults for each variable. Override the values via `docker compose` environment blocks when necessary.

## Agent Roles & Flow

1. **Planner**
   - Decomposes the user goal into a plan (tree or DAG) based on the project state.
   - Stores plan steps in the checkpoint log for resumability.
2. **Executor**
   - Performs tool calls, file edits, or shell commands for each plan step while adhering to path/network guardrails.
   - Emits intermediate observations to the state log and pushes updates to `/workspace`.
3. **Reviewer**
   - Validates that plan steps completed successfully, requests retries if needed, and determines when to stop the run.

**Loop:** Goal → Plan → (Thought → Action → Observation)* → Review → Persist → Exit. Each iteration syncs to `/state` so a restart can resume from the latest checkpoint.

## Tooling Expectations

- **Hosted MCP Tools:** Connect by URL for remote APIs or datasets. Credentials and schemas live alongside tool definitions.
- **Local Tools:** Installed under `/tools` using an internal tool manager; executions inherit the same guardrails (filesystem sandbox, command allowlist, logging).
- **Logging:** Every tool call is timestamped, includes provenance (version/hash), and is appended to `/state/audit/`.
- **Policies:** YAML bundles in `policies/{tools,network,paths}.yaml` define command allowlists, glob rules, and tool/token budgets. Validate with `python -m agent policies validate`; reload live config via `python -m agent policies reload` or the dashboard `POST /policies/reload` endpoint.
- **MCP Connectivity:** `python -m agent mcp health` summarizes endpoint status/latency; invoke remote tools with `python -m agent mcp invoke <endpoint> <tool> --payload '{...}'`. All invocations emit `mcp_invoke` events to the audit log.

## Operational Runbook

1. Launch LM Studio: `lmstudio server --port 1234`.
2. Build + start the container: `docker compose up -d`.
3. Provide a goal: `docker exec -it dev-agent python -m agent "Describe workspace"`.
4. Inspect `/state` for logs/checkpoints or `/workspace` for produced artifacts.
5. Stop the stack when finished: `docker compose down` (state persists in the named volume).

### Quick Operator Commands

| Task | Command |
| --- | --- |
| Policy reload | `python -m agent policies reload` |
| Policy validation | `python -m agent policies validate` |
| Tool listing | `python -m agent tools list` |
| MCP health | `python -m agent mcp health` |
| Compatibility smoke (Responses) | `python scripts/smoke_test.py` |
| Compatibility smoke (Chat fallback) | `AGENT_FORCE_CHAT_COMPLETIONS=true python scripts/smoke_test.py` |

### Agents vs Chat Fallback

- Auto-detected based on Responses availability, but can be forced via `AGENT_FORCE_CHAT_COMPLETIONS`.
- For LM Studio-only environments, set the flag to `true` and monitor the dashboard `/mcp` cards to ensure remote endpoints remain untouched.
- Nightly CI executes both modes; consult `docs/reports/compatibility-matrix.md` for the current support matrix.

### Release Readiness

- Follow `docs/reports/release-checklist.md` before tagging GA builds. Required artifacts: tool registry snapshot, MCP health dump, policy validation output, dual smoke logs, and chaos/nightly evidence.
- `docs/reports/ga-readiness.md` and `docs/reports/gap-analysis.md` must reflect the latest coverage and residual risks.

## Future Enhancements

- Multi-agent orchestration (Planner/Worker/Reviewer split into isolated services).
- Observability exports (OpenTelemetry, ELK) for long-running sessions.
- Fine-grained policy engine that gates tool/file permissions via declarative YAML.
- Guardrail hooks that integrate lint/test/CI checks before promoting agent changes.
- Advanced chaos workflows (LM Studio outage simulation + MCP throttling) baked into nightly jobs.

Use this file alongside `SpecSheet.md` to keep implementation decisions aligned with the original system goals.
