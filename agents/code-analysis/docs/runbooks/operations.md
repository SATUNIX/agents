# Operations Runbook

## 1. Lifecycle Management

1. **Build & start containers**
   ```bash
   docker compose up -d --build
   ```
   - `dev-agent` runs `python -m agent run`.
   - `dev-agent-dashboard` exposes `http://localhost:7081` for metrics/logs.
2. **Provide a goal**
   ```bash
   docker exec dev-agent python -m agent run "Summarize repo"
   ```
3. **Pause/Resume**
   - Capture the `run_id` printed in `/state/checkpoints`.
   - Resume via `python -m agent checkpoints resume <run_id>`.
4. **Shutdown**
   ```bash
   docker compose down
   ```

## 1a. Policy Reloads

- CLI trigger:
  ```bash
  python -m agent policies reload
  ```
- REST trigger:
  ```bash
  curl -X POST http://localhost:7081/policies/reload
  ```
Both send `SIGHUP` to the main runtime using `/state/agent.pid`.

## 2. Logs & Metrics

- `docker logs dev-agent` → container-level output.
- `/state/audit/run-<run_id>.jsonl` → append-only event stream.
- `/state/metrics.json` → tool latency, token counts, error tallies.
- FastAPI dashboard endpoints:
  - `/health`, `/metrics`, `/runs`, `/logs/<run_id>`, `/checkpoints/<run_id>`, `/mcp`.

## 3. Checkpoint Recovery

1. List checkpoints:
   ```bash
   python -m agent checkpoints list
   ```
2. Inspect latest session snapshot:
   ```bash
   python scripts/checkpoint_demo.py
   ```
3. Resume execution:
   ```bash
   python -m agent checkpoints resume <run_id>
   ```
4. Restarted runs continue from the last saved `current_step` and reapply reviewer validation.

## 4. Network Diagnostics

- Verify LM Studio availability:
  ```bash
  curl -s http://host.docker.internal:1234/v1/models
  ```
- MCP endpoint checks:
  - Inspect `/state/tools/mcp_endpoints.json` for status, rate limits, auth tokens.
  - Use `docker exec dev-agent curl <mcp-url>` for reachability.
- If `ALLOW_NET=false`, network requests are blocked by guardrails—update env var and redeploy if network access is required.

## 5. MCP Health & Invocation

- CLI health check:
  ```bash
  python -m agent mcp health
  ```
- Invoke hosted tools for testing:
  ```bash
  python -m agent mcp invoke http-test summarize --payload '{"path": "README.md"}'
  ```
- Dashboard cards (`/mcp` and `/mcp/health`) show live status, latency, and rate-limit incidents.
  Fields include `throttled` flags and `total_invocations` so operators can spot hot endpoints immediately.

## 8. Log Retention & Archival

- Rotate `/state/audit` and `/state/metrics.json` weekly by copying to long-term storage.
- Store `/state/release_artifacts` (SBOM, Trivy, Cosign) as part of compliance evidence.

## 6. Environment Flags Snapshot

| Variable | Purpose |
| --- | --- |
| `AGENT_POLICY_DIR` | Override location of YAML policy bundle. |
| `AGENT_ALLOWED_COMMANDS` | Comma-delimited command allowlist; supports multi-word entries (e.g., `git status`). |
| `AGENT_FORCE_CHAT_COMPLETIONS` | Force chat-completion fallback even if Responses API is available (useful for LM Studio). |
| `AGENT_CREATE_DIRS` | Set to `false` to prevent auto-creation of workspace/state/tools directories on local hosts. |

## 7. Compatibility Smoke Test

Run the bundled script to ensure both Responses and chat-completion modes function:

```bash
python scripts/smoke_test.py
```

CI can execute the script twice—once with default settings and once with `AGENT_FORCE_CHAT_COMPLETIONS=true`—to track regressions across both backends.
