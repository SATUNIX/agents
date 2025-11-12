"""Common base classes for agent roles."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..context import AgentContext


class AgentRole(ABC):
    """Abstract role that receives a shared context."""

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    @property
    def state(self):
        return self.context.state

    @property
    def config(self):
        return self.context.config

    @property
    def llm(self):
        return self.context.llm


class PlannerResult:
    """Structured response describing the high-level plan."""

    def __init__(self, steps: List[str], raw: str) -> None:
        self.steps = steps
        self.raw = raw


class ExecutionResult:
    """Captures per-step execution context and artifacts."""

    def __init__(self, step: str, observations: List[str] | None = None) -> None:
        self.step = step
        self.observations = observations or []


class AgentPlanner(AgentRole):
    @abstractmethod
    def plan(self, goal: str) -> PlannerResult:  # pragma: no cover - abstract
        raise NotImplementedError


class AgentExecutor(AgentRole):
    @abstractmethod
    def execute(self, step: str) -> ExecutionResult:  # pragma: no cover - abstract
        raise NotImplementedError


class AgentReviewer(AgentRole):
    @abstractmethod
    def review(self, goal: str, plan: PlannerResult, results: List[ExecutionResult]) -> Dict[str, Any]:
        raise NotImplementedError
