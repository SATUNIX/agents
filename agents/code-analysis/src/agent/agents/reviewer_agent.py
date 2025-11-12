"""Reviewer role using the Agents SDK."""

from __future__ import annotations

from typing import Dict

from .base import AgentSession, BaseSDKAgent


class ReviewerAgent(BaseSDKAgent):
    """Validates executor output and decides whether to conclude."""

    def review(self, session: AgentSession) -> Dict[str, str]:
        prompt = (
            "You are the reviewer in a Planner → Executor → Reviewer workflow.\n"
            f"Goal: {session.goal}\n"
            f"Plan Steps: {session.plan_steps}\n"
            f"Observations: {session.observations}\n"
            "Provide a PASS/RETRY verdict. If RETRY, outline the corrective action."
        )
        response = self.ask(prompt)
        session.summary = response
        verdict = "PASS" if "PASS" in response.upper() else "REVIEW"
        payload = {"goal": session.goal, "verdict": verdict, "summary": response}
        self.state.append_event("review_summary", payload)
        self.state.save_checkpoint("review", payload)
        self.state.save_checkpoint("session", session.to_dict())
        return payload
