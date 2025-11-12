"""Base classes for SDK-backed agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

from ..config import AgentConfig
from ..sdk import AgentsGateway
from ..state import StateManager


@dataclass
class AgentSession:
    """Tracks plan, execution notes, and summary for a goal."""

    goal: str
    plan_steps: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    summary: str | None = None
    current_step: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "plan_steps": self.plan_steps,
            "observations": self.observations,
            "summary": self.summary,
            "current_step": self.current_step,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSession":
        return cls(
            goal=data.get("goal", ""),
            plan_steps=list(data.get("plan_steps", [])),
            observations=list(data.get("observations", [])),
            summary=data.get("summary"),
            current_step=int(data.get("current_step", 0)),
        )


class BaseSDKAgent:
    """Shared wiring for planner/executor/reviewer roles."""

    def __init__(self, role_name: str, config: AgentConfig, gateway: AgentsGateway, state: StateManager) -> None:
        self.role_name = role_name
        self.config = config
        self.gateway = gateway
        self.state = state

    def ask(self, prompt: str) -> str:
        self.state.append_event(
            "agent_prompt",
            {"role": self.role_name, "prompt": prompt},
        )
        response = self.gateway.run(self.role_name, prompt)
        self.state.append_event(
            "agent_response",
            {"role": self.role_name, "response": response},
        )
        return response
