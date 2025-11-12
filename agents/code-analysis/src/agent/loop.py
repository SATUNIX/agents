"""Coordinator for the Planner → Executor → Reviewer loop."""

from __future__ import annotations

from .agents.executor_agent import ExecutorAgent
from .agents.planner_agent import PlannerAgent
from .agents.reviewer_agent import ReviewerAgent
from .agents.base import AgentSession
from .context import AgentContext
from .sdk import AgentsGateway


class AgentOrchestrator:
    """Runs the high-level reasoning loop using the Agents SDK."""

    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.gateway = AgentsGateway(
            context.config,
            context.tools,
            context.tool_invoker,
            state=context.state,
        )
        self.planner = PlannerAgent("planner", context.config, self.gateway, context.state)
        self.executor = ExecutorAgent("executor", context.config, self.gateway, context.state)
        self.reviewer = ReviewerAgent("reviewer", context.config, self.gateway, context.state)

    def run(self, goal: str) -> None:
        session: AgentSession = self.planner.create_plan(goal)
        self.executor.execute(session, start_index=session.current_step)
        review_summary = self.reviewer.review(session)
        self.context.state.write_audit("latest_review", review_summary)

    def resume(self) -> None:
        session_data = self.context.state.load_checkpoint("session")
        if not session_data:
            raise RuntimeError("No checkpoint available for this run")
        session = AgentSession.from_dict(session_data)
        if not session.plan_steps:
            session = self.planner.create_plan(session.goal or "Review goal")
        if session.current_step < len(session.plan_steps):
            self.executor.execute(session, start_index=session.current_step)
        if session.summary is None:
            review_summary = self.reviewer.review(session)
            self.context.state.write_audit("latest_review", review_summary)
