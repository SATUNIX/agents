# Troubleshooting & Diagnostics

## Common Issues

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| `/usr/local/bin/python: No module named agent` | Container dependencies missing editable install | Ensure Docker build ran after latest changes (`docker compose build`). |
| `GuardrailViolation: Command 'curl' is not allowed` | `ALLOW_NET=false` or command not whitelisted | Update env vars / guardrail config, or use approved commands (`ls`, `cat`, `python`, `pytest`, `rg`, `git status`). |
| `Unknown agent profile` | Missing entry in `config/settings.yaml` | Define agent/tool/policy block, redeploy. |
| Failing MCP health | Endpoint offline or missing token | Regenerate secrets, confirm URLs in `/state/tools/mcp_endpoints.json`. |

## Debug Checklist

1. **Validate config**
   ```bash
   python -m agent config view
   ```
2. **Inspect latest log tail**
   ```bash
   tail -n 100 /state/audit/run-$(ls /state/audit | tail -n1)
   ```
3. **Check metrics anomalies** (spikes in `errors.tool` or latency) via dashboard.
4. **Replay run** using `python -m agent checkpoints resume <run_id>` to reproduce issues.
5. **Capture SBOM + Trivy outputs** for security reviews from `/state/release_artifacts`.
