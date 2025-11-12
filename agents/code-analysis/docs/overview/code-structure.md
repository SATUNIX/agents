# Code Structure

```
src/agent/
├── __main__.py          # Typer CLI (run/resume/config/dashboard/policies/MCP)
├── runtime.py           # AgentRuntime wiring (builds Agent + Runner)
├── config.py            # Pydantic settings, YAML registry, secrets
├── app_agent.py         # Agent definition + HostedMCPTool bindings
├── function_tools.py    # @function_tool definitions (filesystem, shell, repo summary)
├── policies.py          # Policy-as-code loader + budgets + reload hooks
├── state.py             # Metrics/audit logging
├── mcp.py               # Hosted MCP health manager
├── sdk_imports.py       # Imports `openai.agents` with local stub fallback
└── observability/       # FastAPI dashboard
```

### Key Data Classes

- `AgentConfig`: resolves environment, YAML settings, secrets, and directories; produces sanitized snapshots.
- `AgentSession`: (legacy) no longer present; the SDK manages run state internally.
- `StateManager`: append-only JSONL logging, `metrics.json`, `/state/checkpoints`, release artifact helpers.

### Tooling APIs

- `build_function_tools` → returns the SDK-decorated tool callables bound to runtime config/policies.

### Testing & CI Hooks

- `tests/` contains config/tool/state coverage using temp directories.
- GitHub Actions handle lint → type check → pytest plus Docker build, while tag pushes trigger release (SBOM, Trivy, Cosign).
