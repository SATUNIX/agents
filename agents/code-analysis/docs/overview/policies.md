# Policy-as-Code

## File Layout

```
policies/
├── tools.yaml    # command allowlists, tool budgets, per-agent tool lists
├── network.yaml  # allow_net flag, allowed/blocked hosts, rate limits
└── paths.yaml    # allowed/blocked glob patterns inside /workspace
```

Each file is hot-reloadable via `SIGHUP` or REST:

```bash
python -m agent policies reload       # sends SIGHUP via agent.pid
curl -X POST http://localhost:7081/policies/reload  # dashboard endpoint
```

## Budgets

- `tools.yaml > budgets.max_tool_calls` – enforced before every tool invocation.
- `tools.yaml > budgets.max_tokens` – enforced on token accounting in `StateManager`.
- Violations raise `PolicyViolation`, logged as `policy_violation` events.

## Guardrails Integration

- `paths.yaml` drives `Guardrails.ensure_workspace_path` (blocked + allowed globs).
- `tools.yaml > defaults.allowed_commands` drives shell allowlists.
- `network.yaml.allow_net` overrides environment flag for outbound requests.
- `AGENT_ALLOWED_COMMANDS` env var overrides command allowlists at runtime (supports multi-word commands like `git status`).
- `AGENT_POLICY_DIR` points to alternate policy bundles; `AGENT_FORCE_CHAT_COMPLETIONS` can be used alongside policy reloads for LM Studio fallback testing.

## PID + Reload Semantics

- When `python -m agent run` (or `... checkpoints resume`) starts, the runtime writes `/state/agent.pid`.
- Sending `SIGHUP` to that PID reloads YAML policies and updates guardrails without restarting.
- Dashboard `/policies/reload` endpoint and CLI `policies reload` both trigger the same signal.
