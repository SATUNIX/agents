"""Executor role stub that records planned work."""

from __future__ import annotations

from typing import List

from .base import AgentExecutor, ExecutionResult


class ExecutorRole(AgentExecutor):
    """Placeholder executor that logs intent while tools are implemented."""

    def execute(self, step: str) -> ExecutionResult:
        observations: List[str] = [
            "No-op execution (skeleton). Replace with tool integrations.",
        ]
        self.state.append_event("step_executed", {"step": step, "observations": observations})
        return ExecutionResult(step=step, observations=observations)
