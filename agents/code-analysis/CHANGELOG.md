# Changelog

## Unreleased

### Added
- Stage 12–13: Agent SDK now executes local tools via Responses API with policy-aware guardrails, deterministic fallback to chat completions, and compatibility smoke tooling (`scripts/smoke_test.py`, `docs/reports/compatibility-matrix.md`).
- Stage 14: Fully functional MCP client manager (HTTP/WS/STDIO) with CLI + dashboard visibility and audit logging.
- Stage 15: Expanded pytest/CI coverage (runtime, MCP, dashboard, SDK) plus nightly chaos smoke workflow; coverage artifact uploaded from CI.
- Stage 16: Documentation portal refreshed (tool execution demo, runbooks, release checklist, GA readiness updates) and release checklist referencing SDK snapshots + MCP health evidence.
- Stage 1–2: Replaced bespoke LLM/orchestration layers with `openai.agents.Agent` + `Runner`, simplified `AgentConfig`, updated CLI/runtime, and published the SDK compliance snapshot.
- Stage 3–4: Converted local tooling to SDK `@function_tool` definitions, wired Hosted MCP tools via `HostedMCPTool`, streamlined telemetry/guardrails inside each tool, and removed the legacy registry/invoker stack.
