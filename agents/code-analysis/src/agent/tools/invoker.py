"""Executes registered tools with auditing."""

from __future__ import annotations

from typing import Any, Dict
from time import perf_counter

from .base import ToolError
from .registry import ToolRegistry
from ..state import StateManager
from ..policies import PolicyManager, PolicyViolation


class ToolInvoker:
    """Wraps ToolRegistry execution with state logging."""

    def __init__(self, registry: ToolRegistry, state: StateManager, policies: PolicyManager) -> None:
        self.registry = registry
        self.state = state
        self.policies = policies

    def invoke(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.state.append_event("tool_invocation_start", {"tool": tool_name, "payload": payload})
        self.policies.authorize_tool(tool_name)
        start = perf_counter()
        try:
            tool = self.registry.create(tool_name)
            result = tool.run(payload)
            duration = perf_counter() - start
        except ToolError as exc:
            duration = perf_counter() - start
            self.state.append_event(
                "tool_invocation_error", {"tool": tool_name, "error": str(exc)}
            )
            self.state.record_tool_metric(tool_name, duration, success=False)
            raise
        except PolicyViolation as exc:
            duration = perf_counter() - start
            self.state.append_event(
                "policy_violation", {"tool": tool_name, "error": str(exc)}
            )
            self.state.record_tool_metric(tool_name, duration, success=False)
            raise
        self.state.append_event(
            "tool_invocation_complete",
            {"tool": tool_name, "result": result.model_dump()},
        )
        self.state.record_tool_metric(tool_name, duration, success=True)
        return result.model_dump()
