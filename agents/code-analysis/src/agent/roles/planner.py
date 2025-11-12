"""Simple planner role that converts LLM output into actionable steps."""

from __future__ import annotations

import re
from typing import List

from .base import AgentPlanner, PlannerResult


class PlannerRole(AgentPlanner):
    """LLM-backed planner that emits a linear list of steps."""

    def plan(self, goal: str) -> PlannerResult:
        prompt = (
            "You are the planning module of an autonomous engineering agent. "
            "Write a concise numbered list of steps to accomplish the goal below.\n"
            "Goal:\n"
            f"{goal}\n"
            "Steps:"
        )
        raw_plan = self.llm.complete(prompt)
        steps = self._extract_steps(raw_plan)
        self.state.append_event("plan_created", {"goal": goal, "steps": steps})
        return PlannerResult(steps=steps, raw=raw_plan)

    @staticmethod
    def _extract_steps(plan_text: str) -> List[str]:
        matches = re.findall(r"^(?:\d+[.)]|-)\s+(.*)$", plan_text, flags=re.MULTILINE)
        cleaned = [step.strip() for step in matches if step.strip()]
        return cleaned or [plan_text.strip() or "Review goal"]
