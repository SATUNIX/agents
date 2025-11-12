# Development Plan — OpenAI Agents SDK Implementation

This comprehensive roadmap expands upon the existing design specifications and SDK field guide, defining a clear ten-stage development strategy (plus extensions) to evolve the current skeleton into a production-ready, autonomous, Dockerized OpenAI Agents SDK environment.

---

## Stage 1 – Baseline Project Hygiene

**Status:** ✅ Completed – Locked requirements, tooling configs, and automation scaffolding are in place.

Establish robust project hygiene and reproducibility for all environments.

**Objectives:**

* Lock dependency versions using `pip-tools` or `uv`, ensuring deterministic builds.
* Introduce a `pyproject.toml` file with `[tool.ruff]`, `[tool.black]`, and `[tool.mypy]` sections.
* Implement `pre-commit` hooks for linting, formatting, and license compliance.
* Create a standardized developer runner (`Makefile` or `tasks.py`) for installation, testing, and builds.

**Deliverables:**

* `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`.
* Passing lint/test pipelines.

---

## Stage 2 – Containerization and Compose Setup

**Status:** ✅ Completed – Dockerfile, docker-compose stack, and health checks are in place.

**Objectives:**

* Author a hardened Dockerfile with non-root execution, `tini` init process, and bind mounts for `/workspace`, `/state`, `/tools`.
* Define `docker-compose.yaml` linking the agent to LM Studio (via `host.docker.internal` mapping).
* Add automated health checks and proper signal handling (SIGTERM/SIGINT) for graceful shutdown.

**Deliverables:**

* Verified build/run cycle via `docker compose up -d`.
* `docker compose logs -f` shows healthy agent startup.

---

## Stage 3 – Configuration & Secrets Hub

**Status:** ✅ Completed – Typed config, YAML registry, secrets handling, and CLI tooling are ready.

**Objectives:**

* Implement `AgentConfig` using Pydantic to validate and type all configuration inputs.
* Automatically serialize the loaded configuration to `/state/config.json` for traceability.
* Add a central YAML configuration hub that defines agents, models, tools, and policies.
* Introduce secrets handling (env vault or file-based injection with redaction in logs).

**Deliverables:**

* `config.py` and `settings.yaml`.
* CLI command: `python -m agent config view`.

---

## Stage 4 – Core SDK Integration

**Status:** ✅ Completed – Agents SDK bridge, planner/executor/reviewer classes, and orchestrator wiring are live.

**Objectives:**

* Replace the manual chat-completion loop with the official **OpenAI Agents SDK** orchestration model.
* Define standard `Agent`, `Tool`, and `Session` classes.
* Implement `Planner`, `Executor`, and `Reviewer` agents as per SDK conventions.
* Validate LM Studio backend compatibility through the SDK’s response interface.

**Deliverables:**

* SDK-compliant `agent.py` and supporting module hierarchy (`planner.py`, `executor.py`, `reviewer.py`).
* Passing integration tests with local LM Studio model.

---

## Stage 5 – Tooling & MCP Integration Layer

**Status:** ✅ Completed – Local tool registry, MCP bootstrap, and declarative attachments are operational.

**Objectives:**

* Implement Hosted MCP client bootstrap (endpoint discovery, auth, health, rate-limits).
* Create core local tools: `read_file`, `write_file`, `shell_exec`, `repo_summarize`.
* Attach tools declaratively in configuration files with role-based access control.
* Maintain `/state/tools/registry.json` for tool provenance and versioning.

**Deliverables:**

* `tools/` module containing JSON Schema contracts for inputs/outputs.
* Health-checked hosted MCP integrations.

---

## Stage 6 – Security & Guardrails

**Status:** ✅ Completed – Guardrail validators, command/network policies, and reviewer safeguards are wired in.

**Objectives:**

* Enforce path normalization to prevent directory traversal.
* Introduce command and network allowlists tied to `ALLOW_NET` environment flag.
* Apply runtime quotas (CPU, memory, execution time) on subprocess-based tools.
* Implement Reviewer-level guardrails that automatically veto unsafe operations.

**Deliverables:**

* `guardrails.py` module with validators.
* Policy-driven denial tests.

---

## Stage 7 – State Management, Checkpoints & Observability

**Status:** ✅ Completed – JSONL logging, checkpoint resume tooling, and the FastAPI dashboard are live.

**Objectives:**

* Create a JSONL-based append-only log for tool calls and agent messages.
* Implement checkpoint saving/loading under `/state/checkpoints/<run-id>`.
* Add real-time observability via a lightweight FastAPI/Streamlit dashboard (port 7081).
* Record metrics: token counts, tool latency, errors, throughput.

**Deliverables:**

* `/state/audit/run-<timestamp>.jsonl` log files.
* Checkpoint resumption demonstration script.
* Optional monitoring dashboard container.

---

## Stage 8 – Testing & Quality Gates

**Status:** ✅ Completed – Foundational pytest suite, guardrail coverage, and checkpoint tests are in place.

**Objectives:**

* Establish a full Pytest suite covering configuration, tools, planners, and checkpoints.
* Include unit, integration, and end-to-end (E2E) tests using mocked LM Studio/MCP servers.
* Add chaos/fault-injection tests simulating network loss, rate limits, or context truncation.

**Deliverables:**

* `tests/` directory with coverage >90%.
* CI-passing test badge.

---

## Stage 9 – CI/CD & Release Pipeline

**Status:** ✅ Completed – CI lint/test/build and release workflows (with SBOM, scan, signing) are wired up.

**Objectives:**

* Create GitHub Actions (or GitLab CI) workflow for lint → test → build → release.
* Build and publish signed Docker images (`latest`, `dev`, `stable` tags).
* Generate Software Bill of Materials (SBOM) via Syft and vulnerability scan via Trivy.
* Include license compliance verification and provenance signing (SLSA, cosign).

**Deliverables:**

* `.github/workflows/ci.yml` and `.github/workflows/release.yml`.
* SBOM and image signatures stored in `/state/release_artifacts/`.

---

## Stage 10 – Production Hardening & Documentation

**Status:** ✅ Completed – Docs portal, runbooks, QA gap analysis, and GA readiness report delivered.

**Objectives:**

* Transform the SDK Guide and otehr documentation into an organised docs folder with categorised sub folders which explain the codebase and use. 
* Write comprehensive operator runbooks: lifecycle, logs, checkpoint recovery, network diagnostics.
* Conduct testing QA and gap analysis review, adding the gap analysis report into a sub folder in docs.
* Complete final readiness checklist for GA release.

**Deliverables:**

* Thorough documentation folder.
* GA readiness report with SLOs and test results.


Status [ ]

---

## Optional Stage 11 – Policy-as-Code and Extensions

**Status:** ✅ Completed – YAML policy packs, SIGHUP/REST reloads, and budget enforcement are live.

**Objectives:**

* Implement YAML-based policies for tools, paths, and network rules.
* Add runtime reloading of policy files via SIGHUP or REST call.
* Extend to include cost-control budgets and per-run token limits.

**Deliverables:**

* `policies/{tools.yaml, network.yaml, paths.yaml}`.
* Policy validation CLI + SIGHUP/REST reload mechanism.
* Cost-control enforcement (tool-call + token budgets).

---

## Stage 12 – Tool-Backed Execution & Policy Enforcement

**Status:** ✅ Completed – Agents SDK tool-calls now invoke local tools with policy-aware guardrails and structured logging.

**Objectives:**

* Wire Agents SDK tool-calls (function_call / step events) to the local `ToolInvoker`, ensuring planner/executor steps can actually read, write, and shell within `/workspace`.
* Enforce `allowed_globs` / `denied_globs` from `config/settings.yaml` inside each tool and guardrail, so planner claims and policy text match runtime behavior.
* Normalize guardrail command allowlists (per-command entries, environment overrides) and surface policy violations back to reviewer checkpoints for retry loops.

**Deliverables:**

* Updated `AgentsGateway` with tool event handling, retry logic, and structured observation logging.
* Guardrail library that enforces declarative policy rules plus test coverage for accept/reject paths.
* Regression demo (`docs/guides/tool-execution-demo.md`, `scripts/demo_tool_run.py`) showing executor edits and reviewer validation.

---

## Stage 13 – Backend Compatibility & Runtime Safety

**Status:** ✅ Completed – Responses/chat detection, retries, path config, and guardrail enhancements shipped with compatibility docs.

**Objectives:**

* Implement robust feature detection (or config switch) between OpenAI Responses API and chat completions, with graceful fallback when LM Studio lacks Agents endpoints.
* Harden error handling for backend failures (429/5xx), including exponential backoff and token accounting so checkpoints survive transient outages.
* Make workspace/state/tools paths configurable without forcing `/workspace` creation on local hosts; add permission checks and helpful diagnostics.
* Extend command guardrails to support multi-word commands (e.g., `git status`) and provide env-based allowlist overrides for operators.

**Deliverables:**

* Compatibility matrix (`docs/reports/compatibility-matrix.md`) + `scripts/smoke_test.py` smoke script for both modes.
* Updated configuration docs/runbooks describing new env flags and local-development path defaults.
* Guardrail unit tests covering command parsing, network gating, and workspace path validation failures.

---

## Stage 14 – MCP Connectivity & Tool Surfacing

**Status:** ✅ Completed – MCP manager now performs HTTP/WS/STDIO health checks/invocations with CLI + dashboard visibility.

**Objectives:**

* Build actual MCP client connections (HTTP, WS, stdio) with auth token resolution, health probes, and rate-limit tracking per endpoint.
* Surface hosted MCP tools to the planner/executor (via Agents SDK or internal dispatcher) with schema discovery and failure telemetry stored in `/state/audit`.
* Add observability endpoints / dashboard panels summarizing MCP health, quota usage, and last-invocation metadata.

**Deliverables:**

* `MCPClientManager` capable of connecting, authenticating, and invoking sample endpoints end-to-end.
* FastAPI dashboard cards plus CLI commands that show MCP health, throttling status, and actionable remediation hints.
* Integration tests (HTTP + STDIO) validating connection lifecycle, auth/token handling, and rate-limit enforcement.

---

## Stage 15 – Verification, Testing, and QA Alignment

**Status:** ✅ Completed – Coverage expanded (runtime/MCP/dashboard), CI gains coverage artifacts + nightly smoke chaos workflow, docs refreshed.

**Objectives:**

* Expand pytest suite to cover `AgentRuntime`, orchestration checkpoints, tool execution flows, reviewer verdicts, and dashboard endpoints (FastAPI TestClient).
* Add deterministic stubs for the Agents SDK / LM Studio so plan→execute→review cycles can be tested without hitting real endpoints.
* Implement integration + chaos workflows in CI (e.g., nightly job running dockerized agent with induced LM Studio outages, MCP throttling) and report coverage badges.
* Reconcile docs (`gap-analysis`, `ga-readiness`) with measured results, clearly flagging remaining risks if targets are not yet satisfied.

**Deliverables:**

* CI pipelines that run unit, integration, and nightly smoke suites with coverage artifacts uploaded for inspection.
* Coverage reports (pytest-cov + artifact) and compatibility smoke scripts + docs (`compatibility-matrix`, `smoke_test.py`).
* Updated reports/runbooks reflecting true QA status, residual risks, and mitigations tied to this stage.

---

## Stage 16 – Documentation & Release Harmonization

**Status:** ✅ Completed – SpecSheet/AGENTS/docs refreshed, operator guidance expanded, release checklist/change log added.

**Objectives:**

* Refresh `SpecSheet.md`, `AGENTS.md`, and docs portal sections to describe the finalized execution model, MCP tooling, guardrails, and compatibility story.
* Add operator-focused guidance on configuring tool policies, enabling/disabling network access, and troubleshooting Agents-vs-chat fallback behavior.
* Update release workflows/checklists to include new verification artifacts (tool registry snapshots, MCP health dumps, chaos logs) before tagging GA builds.

**Deliverables:**

* Versioned documentation set (SpecSheet, AGENTS, docs portal) describing MCP tooling, guardrails, compatibility story, and operator workflows.
* Release checklist template (`docs/reports/release-checklist.md`) referencing tool registry snapshots, MCP health dumps, and chaos/smoke evidence.
* `CHANGELOG.md` entry summarizing Stages 12–16 with links to the new tests/docs.


Status [ ]

---

## Definition of Done (DoD)

* Agents fully operate through the OpenAI SDK loop.
* LM Studio integration verified via health and response tests.
* Guardrails, policies, and checkpoints function across container restarts.
* All tests, CI/CD pipelines, and audits pass with reproducible results.
* Documentation, observability, and recovery systems are complete and verified.

---

## Future Enhancements

* Multi-agent orchestration (Planner → Worker → Reviewer) with shared registry.
* Vector memory + RAG integration for contextual reasoning.
* Cost-awareness and dynamic model routing (local vs. cloud).
* Integration with OpenTelemetry and Elastic Stack for distributed traces.

---

### Summary

This roadmap represents a full engineering lifecycle from prototype to production readiness, aligning with `SpecSheet.md` and the extended **OpenAI Agents SDK Field Guide**. By completing these stages, the resulting system will be a durable, observable, and extensible autonomous agent platform capable of long-lived reasoning, secure file operations, and continuous development workflows.

Additional Notes: 
Custom “AgentsGateway”/loop that bypasses SDK tool semantics.
Make sure your gateway feeds the SDK (Agents/Responses API) and handles tool call events via your ToolInvoker, rather than inventing a parallel tool protocol.

Homemade tool schema/types.
Keep built-ins to code_interpreter, file_search, and mcp. Everything else should be SDK function tools or Hosted MCP—don’t create a third tool system.

Policy engine that isn’t enforced at runtime.
Your YAML policies must be enforced inside guardrails that wrap every tool execution, not just appended to system prompts.

MCP as a fully custom client before hosted integration.
Prefer Hosted MCP tools first; only add an internal MCP client when you truly need it. Otherwise you risk duplicating plumbing.
Hosted MCP actually live (Stage 14 = planned). Get at least one mature hosted MCP server wired (e.g., GitHub/read-only or Fetch) and visible to the model.

Acceptance tests for tool-calls. Prove end-to-end that the SDK emits tool calls → ToolInvoker runs → outputs are submitted → next step proceeds.

Health probes. One probe to detect Agents/Responses support; another to verify LM Studio readiness; both logged. 





New epics: 
Combine with gap analysis (in progress)
Epic A — Keep the Gateway SDK-True (no parallel protocol)
A1. Server capability probe (Agents/Responses vs Chat)

Tasks

Implement _probe_agents_api() that calls the server (e.g., agents.list() or a lightweight endpoint) and caches result.

Add config override FORCE_CHAT_FALLBACK=true for local/dev.

Emit structured event capability_probe to /state/audit/*.jsonl.

Acceptance

On LM Studio, probe logs agents=false, responses=false, chat=true, and gateway falls back to chat without exceptions.

On OpenAI Agents server, probe logs agents=true, responses=true.

A2. Responses/Agents tool-call execution loop

Tasks

In AgentsGateway.run(...), when using Agents/Responses:

Loop: responses.create(...) → if tool calls present → call ToolInvoker → responses.submit_tool_outputs(...) → repeat until status=completed.

Normalize tool call structure (id/name/arguments) into a stable internal DTO.

Support server-side tools (code_interpreter/file_search/mcp) transparently (no local dispatch).

Acceptance

End-to-end demo where SDK emits a function call → local tool runs → output is submitted → next LLM step succeeds → final text returned.

A3. Chat fallback path (read-only)

Tasks

When falling back to chat completions, disable local tools (clearly warn in logs).

Add a “capabilities banner” to the system prompt (read-only mode).

Acceptance

Chat fallback never attempts tool execution; prompts/outputs persist to audit.

Epic B — Tool Taxonomy (no homemade types)
B1. Restrict built-ins to supported types

Tasks

Enforce: allowed built-ins = {code_interpreter, file_search, mcp}.

Everything else → function tool (schema + handler) or Hosted MCP.

Validate settings.yaml at boot; fail fast on unsupported types.

Acceptance

Invalid type causes a clear startup error with remediation hints.

B2. Function tool schema consistency

Tasks

Single JSON Schema generator for all local tools (Pydantic → JSON Schema).

Tool names normalized (package.module.func → package_module_func).

Acceptance

Schemas appear in agents.create(... tools=[...]); SDK shows identical shapes per run.

Epic C — Policy-as-Code enforced at runtime (not only in prompts)
C1. Guardrails wrapper for every tool execution

Tasks

Wrap ToolInvoker.invoke(...) with:

Path jail: resolve & confirm under /workspace; deny symlink writes.

Command allowlist + shlex.split + which() validation; per-tool time/memory caps.

Network allowlist driven by policy + ALLOW_NET.

Add redaction filter for logs (tokens/URLs with creds).

Acceptance

Attempts to touch ../ or non-allowed commands fail with GuardrailViolation and are logged.

C2. Declarative policy loader + hot-reload

Tasks

policies/{paths.yaml, tools.yaml, network.yaml} → compiled into a single runtime policy object.

SIGHUP/REST reload to swap policies without restart; emit a policy_reload event.

Acceptance

Changing an allowlist at runtime takes effect for next tool call; audit records the policy version.

Epic D — MCP Integration (prefer Hosted MCP first)
D1. Hosted MCP enablement

Tasks

Add env/config to register Hosted MCP servers (label, URL, auth).

Pass them to the SDK using HostedMCPTool entries.

Health probe per MCP server (auth/latency/quota), cached & logged.

Acceptance

At least one mature MCP running (e.g., GitHub read-only or Fetch). The model lists & invokes it; health panel shows green.

D2. Internal MCP client (only if needed)

Tasks

Optional later: generic client for HTTP/WS/stdio with schema discovery.

Rate-limit + backoff + circuit-breaker per MCP endpoint.

Acceptance

Disabled by default; when enabled, telemetry shows rate-limit handling and retries.

Epic E — Acceptance Tests for Tool Calls
E1. Local function tool E2E

Tasks

Test: prompt that forces write_file → assert file created; verify submit_tool_outputs call observed.

Negative: traversal attempt (../../etc/passwd) → assert guardrail denial, no file changed.

Acceptance

Tests pass deterministically; audit contains {tool_call, tool_output, decision} triplets.

E2. Hosted MCP E2E

Tasks

With a hosted Fetch/GitHub MCP:

Prompt to fetch a simple page/repo metadata; assert content summary returned.

Acceptance

MCP result visible in final output; health stats recorded.

Epic F — Health Probes & Readiness
F1. Backend capability probe

Tasks

/healthz returns JSON:

{ agents_api: bool, responses_api: bool, chat_api: bool, lm_studio_reachable: bool }.

Probe on boot and on interval; write results to /state/audit.

Acceptance

Correct detection on LM Studio vs Agents server; 5xx turns health red.

F2. LM Studio readiness probe

Tasks

Ping OPENAI_BASE_URL with a minimal chat request or a /v1/models list (if supported).

Configurable timeout/backoff; expose last OK timestamp in /healthz.

Acceptance

When LM Studio stops, health flips to red within probe window; resumes when back.

Implementation details to copy-paste

Config flags

FORCE_CHAT_FALLBACK, MCP_REGISTRY_PATH, POLICY_DIR, ALLOW_NET, HEALTH_INTERVAL_S.

Telemetry schema (JSONL)

capability_probe, tool_call, tool_output, guardrail_violation, policy_reload, mcp_health, backend_error, checkpoint_saved.

Error taxonomy

GuardrailViolation, ToolError, BackendUnavailable, PolicyDenied, Timeout, RateLimited.

Concrete deliverables

 gateway/capabilities.py — probe + cached capability map

 gateway/run_agents.py — Responses loop with tool-outputs submission

 tools/invoker.py — wraps guardrails, redaction, timing, truncation

 policies/ + policy_loader.py — compile/hot-reload policies

 mcp/hosted_registry.py — load servers → HostedMCPTool list + health

 health/server.py — tiny FastAPI /healthz + /metrics

 tests/e2e_tool_calls.py — positive & negative local tool flows

 tests/e2e_mcp.py — hosted MCP happy-path test

 docs/guides/tool-execution-demo.md — step-by-step demo

Definition of Done for this expansion

Gateway always prefers SDK Agents/Responses when available; chat path is read-only fallback.

Tool calls from SDK are executed by ToolInvoker with runtime guardrails; outputs are submitted back to the SDK until completion.

Hosted MCP tool(s) are live, discoverable, and visible in the model’s tool list.

Policies are enforced, hot-reloadable, and audited.

Health probes report backend/MCP readiness and flip on failure.

E2E tests prove the loop: SDK tool call → ToolInvoker → submit tool outputs → next step → final answer.
