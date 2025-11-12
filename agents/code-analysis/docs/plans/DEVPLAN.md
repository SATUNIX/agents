# DEVPLAN — OpenAI Agents SDK Alignment

Goal: Delete custom orchestration/tooling layers and rebuild the repo around the official OpenAI Agents Python SDK primitives (`Agent`, `Runner`, `@function_tool`, `HostedMCPTool`). Each epic below lists the files to refactor/remove, the SDK feature that replaces them, and the acceptance criteria.

## Epic 1 (Done): Establish SDK Foundation & Dependencies
- **Tasks**
  1. Replace bespoke LLM wrappers with the official SDK client. Update `pyproject.toml`/`requirements.*` to depend on `openai-agents` and remove redundant packages (`sdk.py`, `llm.py`).
  2. Rewrite `AgentConfig` to expose only environment + policy settings required by the official SDK. Drop custom OpenAI fallback logic now handled by the library.
  3. Update `docs/reports/OPENAI_AGENTS_COMPLIANCE.md` with the compliance snapshot once the SDK becomes the single orchestration layer.
- **Acceptance Criteria**
  - Importing `from openai.agents import Agent, Runner` succeeds and no local wrappers call `openai.OpenAI` directly.
  - Config module no longer references `src/agent/sdk.py` or chat-completion fallbacks; SDK handles backend selection.
  - Compliance doc shows zero “custom orchestration” issues.

## Epic 2 (Done): Rebuild Runtime & Orchestration with `Agent`/`Runner`
- **Tasks**
  1. Delete `src/agent/loop.py`, `src/agent/agents/*`, and `AgentOrchestrator`. Define a single `Agent` (or multiple roles if needed) using SDK-native planners/workflows.
  2. Replace `AgentRuntime` with a thin `Runner` launcher that wires config + telemetry into SDK hooks. Remove `AgentSession`/checkpoint logic duplicated by the SDK.
  3. Convert CLI commands (`src/agent/__main__.py`) to call `Runner.run()`/`Runner.resume()` instead of custom planners/executors.
- **Acceptance Criteria**
  - Running `python -m agent run "..."` executes via `Runner` without touching legacy modules.
  - Checkpoint/resume flows rely on SDK persistence features (or wrappers around them) rather than `StateManager` plan snapshots.
  - Deleted files no longer referenced anywhere in the codebase.

## Epic 3 (Done): Convert Tools to `@function_tool` & `HostedMCPTool`
- **Highlights**
  1. `src/agent/function_tools.py` now exposes the filesystem/shell/repo tools via `@function_tool`, each with inline guardrails + telemetry.
  2. Hosted integrations are declared through `HostedMCPTool` entries in `src/agent/app_agent.py`; `MCPClientManager` only handles health snapshots.
  3. Docs/runbooks describe how to add new function tools or hosted MCP definitions using the SDK syntax.
- **Acceptance Criteria**
  - Tools are registered solely via SDK decorators.
  - Hosted MCP endpoints surface as `HostedMCPTool` instances consumed directly by the SDK.
  - Documentation references `@function_tool` guidance instead of legacy registries.

## Epic 4 (Done): Telemetry, Guardrails, and Health Hooks
- **Highlights**
  1. `StateManager` ingests `tool_call` events directly from the function tools + Runner lifecycle (run/resume) rather than bespoke loops.
  2. Guardrails now live inside the tool implementations (path jail + command/network allowlists), removing the global guardrails wrapper.
  3. Dashboard endpoints continue to serve metrics/logs/MCP health without referencing deleted modules.
- **Acceptance Criteria**
  - Every SDK tool invocation logs an audit entry via the shared helper.
  - Guardrail logic exists only inside `function_tools.py`.
  - Dashboard remains operational with the new telemetry sources.

## Epic 5: Documentation & Release Harmonization
- **Tasks**
  1. Rewrite `SpecSheet.md`, `AGENTS.md`, and docs portal pages to describe the SDK-native architecture (Agent/Runner, SDK tools, Hosted MCP). Remove descriptions of the deprecated custom orchestrator.
  2. Update runbooks to show SDK commands (e.g., `@function_tool` examples, `HostedMCPTool` configuration) and troubleshooting steps for Responses vs chat fallback in the SDK.
  3. Refresh release collateral (`docs/reports/ga-readiness.md`, `docs/reports/release-checklist.md`, `CHANGELOG.md`) to note that the migration to the official SDK is complete and legacy modules are removed.
- **Acceptance Criteria**
  - Documentation contains only SDK terminology; no references to removed files (`loop.py`, `ToolRegistry`, `AgentSession`).
  - Release checklist includes verification of SDK tool registration and hosted MCP health via SDK APIs.
  - Dev plan, compliance report, and changelog collectively reflect the simplified, SDK-native system.



Also noted: Requirement already satisfied: pycparser in i:\ai\agents\agents\code-analysis\.venv\lib\site-packages (from cffi>=2.0.0->cryptography>=3.4.0->pyjwt[crypto]>=2.10.1->mcp<2,>=1.11.0->openai-agents) (2.23)
Requirement already satisfied: click>=7.0 in i:\ai\agents\agents\code-analysis\.venv\lib\site-packages (from uvicorn>=0.31.1->mcp<2,>=1.11.0->openai-agents) (8.1.7)
(.venv) PS I:\AI\agents\agents\code-analysis> pytest  -q
ImportError while loading conftest 'I:\AI\agents\agents\code-analysis\tests\conftest.py'.
tests\conftest.py:10: in <module>
    from agent.config import AgentConfig
E   ModuleNotFoundError: No module named 'agent'
(.venv) PS I:\AI\agents\agents\code-analysis>

Also: to rename repo to avoid conflict
Fix import of local modules for tests (rename agent folder to something different)
Open AI Agent library = agents
Repo = agent-collections
src/agents to = main

Todo reminder: re anlyse and review codebase, perform tests, write review report, make a new plan as necessary. 