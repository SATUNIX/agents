"""Factory methods for wiring configuration/state/context."""

from __future__ import annotations

from .config import AgentConfig
from .context import AgentContext
from .llm import LLMClient
from .loop import AgentOrchestrator
from .state import StateManager


class AgentRuntime:
    """Builds the orchestrator and exposes a simple run() helper."""

    def __init__(self) -> None:
        config = AgentConfig.load()
        state = StateManager(config.state_dir)
        llm = LLMClient(config)
        context = AgentContext(config=config, state=state, llm=llm)
        self._orchestrator = AgentOrchestrator(context)

    def run(self, goal: str) -> None:
        self._orchestrator.run(goal)
