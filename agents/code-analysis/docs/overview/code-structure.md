# Code Structure

```
src/agent/
├── __main__.py          # Typer CLI (run/resume/tools/config/dashboard)
├── runtime.py           # AgentRuntime wiring (builds Agent + Runner)
├── config.py            # Pydantic settings, YAML registry, secrets
├── loop.py              # Planner → Executor → Reviewer orchestrator
├── agents/              # (Legacy) – removed in SDK alignment (see plan)
├── function_tools.py    # @function_tool definitions (filesystem, shell, repo summary)
├── guardrails.py        # Path + command policies
├── policies.py          # Policy-as-code loader + budgets + reload hooks
├── state.py             # Metrics, checkpoints, audit logging
├── mcp.py               # Hosted MCP endpoint metadata
├── sdk.py               # OpenAI Agents SDK gateway with fallbacks
└── observability/       # FastAPI dashboard
```

### Key Data Classes

- `AgentConfig`: resolves environment, YAML settings, secrets, and directories; produces sanitized snapshots.
- `AgentSession`: (legacy) replaced by the SDK's internal run-tracking — see DEVPLAN Epic 2.
- `StateManager`: append-only JSONL logging, `metrics.json`, `/state/checkpoints`, release artifact helpers.

### Tooling APIs

- `build_function_tools` → returns the SDK-decorated tool callables bound to runtime config/policies.

### Testing & CI Hooks

- `tests/` contains config/tool/guardrail/state coverage using temp directories.
- GitHub Actions handle lint → type check → pytest plus Docker build, while tag pushes trigger release (SBOM, Trivy, Cosign).
