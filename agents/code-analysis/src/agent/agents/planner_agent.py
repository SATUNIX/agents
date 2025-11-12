"""Planner role implemented via the Agents SDK."""

from __future__ import annotations

import re
from typing import List

from .base import AgentSession, BaseSDKAgent


class PlannerAgent(BaseSDKAgent):
    """Generates a sequenced plan for the given goal."""

    def create_plan(self, goal: str) -> AgentSession:
        prompt = (
            "You are the planning module in a Planner → Executor → Reviewer workflow. "
            "Break the user's goal into 3-7 numbered steps. Each step should be actionable, "
            "reference the tools you expect to use, and specify completion criteria.\n\n"
            f"Goal:\n{goal}\n\nSteps:"
        )
        response = self.ask(prompt)
        steps = self._extract_steps(response)
        session = AgentSession(goal=goal, plan_steps=steps)
        payload = {"goal": goal, "steps": steps}
        self.state.append_event("plan_created", payload)
        self.state.save_checkpoint("plan", payload)
        self.state.save_checkpoint("session", session.to_dict())
        return session

    @staticmethod
    def _extract_steps(raw: str) -> List[str]:
        matches = re.findall(r"^(?:\d+[.)]|-)\s+(.*)$", raw, flags=re.MULTILINE)
        cleaned = [step.strip() for step in matches if step.strip()]
        return cleaned or [raw.strip() or "Review goal"]
