"""Reviewer role stub that evaluates executor output."""

from __future__ import annotations

from typing import Dict, List

from .base import AgentReviewer, ExecutionResult, PlannerResult


class ReviewerRole(AgentReviewer):
    """Basic reviewer that records completion status for observability."""

    def review(self, goal: str, plan: PlannerResult, results: List[ExecutionResult]) -> Dict[str, str]:
        status = "completed" if len(results) == len(plan.steps) else "incomplete"
        summary = {
            "goal": goal,
            "status": status,
            "executed_steps": [result.step for result in results],
        }
        self.state.append_event("review_complete", summary)
        return summary
