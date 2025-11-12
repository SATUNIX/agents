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

Currently this submits a descriptive goal through the SDK Runner (the forthcoming `@function_tool` refactor will reintroduce explicit file edits here).

## 3. Validate via Reviewer

After running the demo, launch a normal agent goal:

```bash
docker exec dev-agent python -m agent run "Review workspace"
```

Once the SDK-native tools are in place, the reviewer will validate actual file diffs; for now this confirms the Runner wiring.

## 4. Observability

- Visit `http://localhost:7081/logs/<run_id>` to inspect tool invocation entries.
- Use `python -m agent checkpoints resume <run_id>` to replay the run from the last saved step.
