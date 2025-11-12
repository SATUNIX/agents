# GA Release Checklist

1. **Policy & Config Validation**
   - `python -m agent policies validate`
   - `python -m agent config view > state/release_artifacts/config.json`

2. **Tool Registry Snapshot**
   - Run `python -m agent tools list > state/release_artifacts/tools.txt`.
   - Ensure `state/tools/registry.json` is archived with the release artifacts.

3. **MCP Health Dump**
   - `python -m agent mcp health > state/release_artifacts/mcp_health.json`.
   - For each critical endpoint, run `python -m agent mcp invoke ...` with a dry-run payload and capture the output.

4. **Compatibility Smoke**
   - `python scripts/smoke_test.py`
   - `AGENT_FORCE_CHAT_COMPLETIONS=true python scripts/smoke_test.py`
   - Attach both logs to `/state/release_artifacts/` (e.g., `responses_smoke.log`, `chat_smoke.log`).

5. **Chaos/Nightly Evidence**
   - Collect the latest nightly workflow outcome (URL + log snippet) and store under `/state/release_artifacts/chaos.log`.

6. **MCP/Tool Invocation Audit**
   - Copy recent `/state/audit/run-<id>.jsonl` entries showing tool-backed execution and MCP invocations.

7. **Sign-off Rubric**
   - ✅ Docs portal updated (architecture, guides, runbooks, reports).
   - ✅ Release artifacts archived: SBOM, Trivy, Cosign, tool registry snapshot, MCP health dump, smoke logs.
   - ✅ Outstanding risks documented in `docs/reports/ga-readiness.md` and `docs/reports/gap-analysis.md`.
   - ☐ Coverage badge published (pending action if unchecked).
