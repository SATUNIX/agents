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
   - Capture the `run_id` emitted by the SDK (printed in the Runner logs).
   - Resume via `python -m agent resume <run_id>` (delegates to `Runner.resume`).
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

The official SDK manages persistence internally. To resume a run:

```bash
python -m agent resume <run_id>
```

If you need to inspect the raw storage, look under `/state` (the SDK stores metadata in provider-specific directories); `scripts/checkpoint_demo.py` can still dump recent audit entries for reference.

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
- To exercise a hosted tool, run a goal that references it (e.g., `python -m agent run "Use http-test to summarize README"`) and inspect `/state/audit` for the resulting tool call.
- Dashboard cards (`/mcp` and `/mcp/health`) show live status, latency, rate-limit incidents, `throttled` flags, and `total_invocations` so operators can spot hot endpoints immediately.

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

CI/nightly also runs the script with `AGENT_FORCE_CHAT_COMPLETIONS=true` to track regressions across both backends.

## 8. Agents vs Chat Troubleshooting

- If Responses mode fails, set `AGENT_FORCE_CHAT_COMPLETIONS=true` and rerun `scripts/smoke_test.py` to confirm fallback.
- Expect `/state/tools/mcp_endpoints.json` and dashboard cards to show zero remote invocations when running chat-only.
- Revalidate policies (`python -m agent policies validate`) whenever toggling modes to ensure guardrails remain synchronized.

## 9. Log Retention & Archival

- Rotate `/state/audit` and `/state/metrics.json` weekly by copying to long-term storage.
- Store `/state/release_artifacts` (SBOM, Trivy, Cosign, SDK snapshot, MCP health dump, smoke logs) as part of compliance evidence.
- **Adding a new tool**
  - Define it in `src/agent/function_tools.py` using `@function_tool` and capture `config/policies/state` for guardrails + telemetry.
  - Rebuild the agent (`build_agent`) automatically picks up the function when returned in `build_function_tools`.
  - For hosted integrations, append a `HostedMCPTool` entry via `config/settings.yaml`.
