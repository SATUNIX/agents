# Code Structure

```
src/agent/
├── __main__.py          # Typer CLI (run/resume/tools/config/dashboard)
├── runtime.py           # AgentRuntime wiring
├── config.py            # Pydantic settings, YAML registry, secrets
├── loop.py              # Planner → Executor → Reviewer orchestrator
├── agents/              # SDK-backed role implementations
├── tools/               # Local tool framework + registry/invoker
├── guardrails.py        # Path + command policies
├── policies.py          # Policy-as-code loader + budgets + reload hooks
├── state.py             # Metrics, checkpoints, audit logging
├── mcp.py               # Hosted MCP endpoint metadata
├── sdk.py               # OpenAI Agents SDK gateway with fallbacks
└── observability/       # FastAPI dashboard
```

### Key Data Classes

- `AgentConfig`: resolves environment, YAML settings, secrets, and directories; produces sanitized snapshots.
- `AgentSession`: tracks plan steps, observations, summary, current step for checkpointing.
- `StateManager`: append-only JSONL logging, `metrics.json`, `/state/checkpoints`, release artifact helpers.

### Tooling APIs

- `ToolContext` → gives each tool access to configuration.
- `LocalTool` → base class with schema validation, guardrails, `_run_shell`, `_within_workspace` helpers.
- `ToolRegistry` → registers local tools, surfaces JSON Schema metadata to the Agents SDK.
- `ToolInvoker` → executes tools with auditing and latency metrics.

### Testing & CI Hooks

- `tests/` contains config/tool/guardrail/state coverage using temp directories.
- GitHub Actions handle lint → type check → pytest plus Docker build, while tag pushes trigger release (SBOM, Trivy, Cosign).
