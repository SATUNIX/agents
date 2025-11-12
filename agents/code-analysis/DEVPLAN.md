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

**Status:** 🚧 Planned – Bridges the current reasoning-only executor with the filesystem/tooling expectations in SpecSheet/AGENTS.

**Objectives:**

* Wire Agents SDK tool-calls (function_call / step events) to the local `ToolInvoker`, ensuring planner/executor steps can actually read, write, and shell within `/workspace`.
* Enforce `allowed_globs` / `denied_globs` from `config/settings.yaml` inside each tool and guardrail, so planner claims and policy text match runtime behavior.
* Normalize guardrail command allowlists (per-command entries, environment overrides) and surface policy violations back to reviewer checkpoints for retry loops.

**Deliverables:**

* Updated `AgentsGateway` with tool event handling, retry logic, and structured observation logging.
* Guardrail library that enforces declarative policy rules plus test coverage for accept/reject paths.
* Regression demo where the executor edits a file using local tools and the reviewer validates the diff.

---

## Stage 13 – Backend Compatibility & Runtime Safety

**Status:** 🚧 Planned – Resolves the LM Studio / Agents SDK mismatch and hard-coded workspace assumptions.

**Objectives:**

* Implement robust feature detection (or config switch) between OpenAI Responses API and chat completions, with graceful fallback when LM Studio lacks Agents endpoints.
* Harden error handling for backend failures (429/5xx), including exponential backoff and token accounting so checkpoints survive transient outages.
* Make workspace/state/tools paths configurable without forcing `/workspace` creation on local hosts; add permission checks and helpful diagnostics.
* Extend command guardrails to support multi-word commands (e.g., `git status`) and provide env-based allowlist overrides for operators.

**Deliverables:**

* Compatibility matrix + automated smoke test proving both LM Studio chat-only and OpenAI Responses modes succeed.
* Updated configuration docs/runbooks describing new env flags and local-development path defaults.
* Guardrail unit tests covering command parsing, network gating, and workspace path validation failures.

---

## Stage 14 – MCP Connectivity & Tool Surfacing

**Status:** 🚧 Planned – Converts the MCP placeholder into a functioning integration tier.

**Objectives:**

* Build actual MCP client connections (HTTP, WS, stdio) with auth token resolution, health probes, and rate-limit tracking per endpoint.
* Surface hosted MCP tools to the planner/executor (via Agents SDK or internal dispatcher) with schema discovery and failure telemetry stored in `/state/audit`.
* Add observability endpoints / dashboard panels summarizing MCP health, quota usage, and last-invocation metadata.

**Deliverables:**

* `MCPClientManager` capable of connecting, authenticating, and invoking sample endpoints end-to-end.
* FastAPI dashboard cards plus CLI commands that show MCP health, throttling status, and actionable remediation hints.
* Integration tests using mocked MCP servers validating connection lifecycle, auth failures, and rate-limit enforcement.

---

## Stage 15 – Verification, Testing, and QA Alignment

**Status:** 🚧 Planned – Aligns real coverage with the GA claims in docs/reports.

**Objectives:**

* Expand pytest suite to cover `AgentRuntime`, orchestration checkpoints, tool execution flows, reviewer verdicts, and dashboard endpoints (FastAPI TestClient).
* Add deterministic stubs for the Agents SDK / LM Studio so plan→execute→review cycles can be tested without hitting real endpoints.
* Implement integration + chaos workflows in CI (e.g., nightly job running dockerized agent with induced LM Studio outages, MCP throttling) and report coverage badges.
* Reconcile docs (`gap-analysis`, `ga-readiness`) with measured results, clearly flagging remaining risks if targets are not yet satisfied.

**Deliverables:**

* CI pipelines that run unit, integration, and chaos suites with artifacts uploaded for inspection.
* Coverage reports (e.g., `pytest --cov`) published to README/docs plus alerts if thresholds regress.
* Updated reports/runbooks reflecting true QA status, residual risks, and mitigations tied to this stage.

---

## Stage 16 – Documentation & Release Harmonization

**Status:** 🚧 Planned – Ensures project collateral matches the implemented reality once Stages 12–15 land.

**Objectives:**

* Refresh `SpecSheet.md`, `AGENTS.md`, and docs portal sections to describe the finalized execution model, MCP tooling, guardrails, and compatibility story.
* Add operator-focused guidance on configuring tool policies, enabling/disabling network access, and troubleshooting Agents-vs-chat fallback behavior.
* Update release workflows/checklists to include new verification artifacts (tool registry snapshots, MCP health dumps, chaos logs) before tagging GA builds.

**Deliverables:**

* Versioned documentation set (overview, guides, runbooks, reports) that tracks the enhanced stages and links to real evidence.
* Release checklist template referencing the new verification data and a sign-off rubric for GA readiness.
* Change log entry summarizing the completion of Stages 12–16 with cross-links to relevant docs/tests.

* `policies/{tools.yaml, network.yaml, paths.yaml}`.
* Policy validation CLI and reload signal handler.


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
