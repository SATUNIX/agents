"""Factory methods for wiring configuration/state/context."""

from __future__ import annotations

from .config import AgentConfig
from .context import AgentContext
from .llm import LLMClient
from .loop import AgentOrchestrator
from .state import StateManager
from .tools import ToolContext
from .tools.registry import ToolRegistry
from .tools.invoker import ToolInvoker
from .mcp import MCPClientManager


class AgentRuntime:
    """Builds the orchestrator and exposes run/resume helpers."""

    def __init__(self, run_id: str | None = None) -> None:
        config = AgentConfig.load()
        config.write_snapshot()
        state = StateManager(config.state_dir, run_id=run_id)
        llm = LLMClient(config)
        tool_context = ToolContext(config)
        tool_registry = ToolRegistry(tool_context)
        tool_registry.write_registry(config.state_dir / "tools" / "registry.json")
        tool_invoker = ToolInvoker(tool_registry, state)
        mcp_manager = MCPClientManager(config)
        mcp_manager.write_snapshot(config.state_dir / "tools" / "mcp_endpoints.json")
        self.context = AgentContext(
            config=config,
            state=state,
            llm=llm,
            tools=tool_registry,
            tool_invoker=tool_invoker,
            mcp=mcp_manager,
        )
        self._orchestrator = AgentOrchestrator(self.context)

    def run(self, goal: str) -> None:
        self._orchestrator.run(goal)

    def resume(self) -> None:
        self._orchestrator.resume()
