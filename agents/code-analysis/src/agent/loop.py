"""Coordinator for the Planner → Executor → Reviewer loop."""

from __future__ import annotations

from typing import List

from .context import AgentContext
from .roles.base import ExecutionResult, PlannerResult
from .roles.executor import ExecutorRole
from .roles.planner import PlannerRole
from .roles.reviewer import ReviewerRole


class AgentOrchestrator:
    """Runs the high-level reasoning loop."""

    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.planner = PlannerRole(context)
        self.executor = ExecutorRole(context)
        self.reviewer = ReviewerRole(context)

    def run(self, goal: str) -> None:
        plan = self.planner.plan(goal)
        results: List[ExecutionResult] = []
        for step in plan.steps:
            result = self.executor.execute(step)
            results.append(result)
        review_summary = self.reviewer.review(goal, plan, results)
        self.context.state.write_audit("latest_review", review_summary)
