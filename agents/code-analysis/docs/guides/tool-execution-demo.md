# Tool-Backed Execution Demo

This walkthrough exercises the executor’s ability to edit files via local tools and validates the outcome with the reviewer role.

## 1. Prepare Environment

```bash
docker compose up -d --build
```

## 2. Run the Demo Script

```bash
docker exec dev-agent python scripts/demo_tool_run.py
```

This uses the SDK-native `@function_tool` definitions in `src/agent/function_tools.py` (read/write/shell/repo summary). The runner will call those tools when needed.

## 3. Validate via Reviewer

After running the demo, launch a normal agent goal:

```bash
docker exec dev-agent python -m agent run "Review workspace"
```

The reviewer validates actual file diffs (since the runner now leverages the function tools). Inspect `/state/audit` to see `tool_call` entries.

## 4. Observability

- Visit `http://localhost:7081/logs/<run_id>` to inspect tool invocation entries.
- Use `python -m agent checkpoints resume <run_id>` to replay the run from the last saved step.
