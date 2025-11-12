"""Fallback stubs for the OpenAI Agents SDK (used when dependency is unavailable)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, List


class Agent:
    def __init__(self, *, name: str, instructions: str, model: str, tools: Iterable[Any] | None = None):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = list(tools or [])


class Runner:
    def __init__(self, agent: Agent):
        self.agent = agent
        self._history: List[str] = []

    def run(self, goal: str) -> None:
        self._history.append(goal)

    def resume(self, run_id: str | None = None) -> None:
        self._history.append(f"resume:{run_id}")


def function_tool(func: Callable | None = None, **_: Any) -> Callable:
    def decorator(fn: Callable) -> Callable:
        return fn

    return decorator(func) if func else decorator


@dataclass
class HostedMCPTool:
    name: str
    transport: str
    url: str | None = None
    command: str | None = None
    args: List[str] | None = None
    auth_token_env: str | None = None
