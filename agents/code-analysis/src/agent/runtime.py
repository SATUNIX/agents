"""Factory methods for wiring configuration/state/context."""

from __future__ import annotations

import signal

from .config import AgentConfig
from .context import AgentContext
from .llm import LLMClient
from .loop import AgentOrchestrator
from .state import StateManager
from .tools import ToolContext
from .tools.registry import ToolRegistry
from .tools.invoker import ToolInvoker
from .mcp import MCPClientManager
from .policies import PolicyManager
from .guardrails import Guardrails


class AgentRuntime:
    """Builds the orchestrator and exposes run/resume helpers."""

    def __init__(self, run_id: str | None = None) -> None:
        config = AgentConfig.load()
        config.write_snapshot()
        policy_manager = PolicyManager(config.policy_dir)
        state = StateManager(config.state_dir, run_id=run_id, policy_manager=policy_manager)
        llm = LLMClient(config)
        guardrails = Guardrails(config, policy_manager)
        tool_context = ToolContext(config, guardrails, policy_manager)
        tool_registry = ToolRegistry(tool_context)
        tool_registry.write_registry(config.state_dir / "tools" / "registry.json")
        tool_invoker = ToolInvoker(tool_registry, state, policy_manager)
        mcp_manager = MCPClientManager(config, state=state)
        mcp_manager.write_snapshot(config.state_dir / "tools" / "mcp_endpoints.json")
        self.context = AgentContext(
            config=config,
            state=state,
            llm=llm,
            tools=tool_registry,
            tool_invoker=tool_invoker,
            mcp=mcp_manager,
            policies=policy_manager,
            guardrails=guardrails,
        )
        self._orchestrator = AgentOrchestrator(self.context)
        signal.signal(signal.SIGHUP, self._handle_reload)
        self.context.policies.write_pid()

    def run(self, goal: str) -> None:
        self.context.policies.write_pid()
        self._orchestrator.run(goal)

    def resume(self) -> None:
        self.context.policies.write_pid()
        self._orchestrator.resume()

    def _handle_reload(self, signum, frame):  # pragma: no cover - signal handler
        self.context.policies.reload()
        self.context.guardrails.policies = self.context.policies
