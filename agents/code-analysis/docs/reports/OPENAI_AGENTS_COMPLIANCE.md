# OpenAI Agents SDK Compliance Report

_Last updated: 2025-11-12_

- ✅ **Single Orchestration Layer** – The project now constructs a single `openai.agents.Agent` (see `src/agent/app_agent.py`) and runs it via `openai.agents.Runner` (`src/agent/runtime.py`). All bespoke planner/executor/reviewer loops (`loop.py`, `agents/`, `sdk.py`) have been removed.
- ✅ **No Direct `openai.OpenAI` Usage** – Custom LLM wrappers (`llm.py`) and chat-completion fallbacks were deleted. The SDK controls model selection and backend negotiation.
- ✅ **Policy & Telemetry Hooks** – `PolicyManager`/`StateManager` now listen to Runner events rather than wrapping their own orchestration, preserving guardrails without interfering with SDK flow.
- ✅ **Hosted MCP Integration** – Hosted endpoints are surfaced through `HostedMCPTool` inside the Agent definition. The legacy MCP invoker exists only as a health/telemetry helper.
- ✅ **Function Tool Migration** – Local filesystem tools now use `@function_tool` decorators (see `src/agent/function_tools.py`); Hosted MCP tools are declared via the SDK’s `HostedMCPTool`.

No outstanding “custom orchestration” issues remain.
