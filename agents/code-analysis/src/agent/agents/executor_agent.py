"""Executor role implemented through the Agents SDK."""

from __future__ import annotations

from typing import List

from .base import AgentSession, BaseSDKAgent


class ExecutorAgent(BaseSDKAgent):
    """Walks through each plan step and records observations."""

    def execute(self, session: AgentSession, start_index: int = 0) -> List[str]:
        observations: List[str] = session.observations[:]
        for offset, step in enumerate(session.plan_steps[start_index:], start=start_index + 1):
            prompt = (
                f"You are executing step {offset} of a plan for the goal: {session.goal}.\n"
                f"Step description: {step}.\n"
                "Describe the concrete actions you performed, cite any tools used, and provide"
                " artifacts or file changes that resulted."
            )
            response = self.ask(prompt)
            observations.append(response)
            session.observations = observations
            session.current_step = offset
            self.state.save_checkpoint("session", session.to_dict())
        self.state.append_event(
            "execution_complete",
            {"goal": session.goal, "observations": observations, "completed_steps": session.current_step},
        )
        self.state.save_checkpoint("execution", session.to_dict())
        return observations
