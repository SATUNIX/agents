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

What happens:

1. The script instantiates `AgentRuntime`, which loads policies and writes `demo.txt` via `workspace.write_file`.
2. The script immediately reads the file back via `workspace.read_file` and prints the contents.
3. A `demo_tool_run` event is appended to `/state/audit/run-<run_id>.jsonl`, capturing the tool output.

## 3. Validate via Reviewer

After running the demo, launch a normal agent goal:

```bash
docker exec dev-agent python -m agent run "Review demo.txt changes"
```

The reviewer sees the tool-backed edits (since the executor can now invoke tools from Agents SDK function-calls) and validates the diff before completing the run. Check `/state/checkpoints/<run_id>/session.json` to confirm the reviewer summary includes the file inspection.

## 4. Observability

- Visit `http://localhost:7081/logs/<run_id>` to inspect tool invocation entries.
- Use `python -m agent checkpoints resume <run_id>` to replay the run from the last saved step.
