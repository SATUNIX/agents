"""Shared context passed to role implementations."""

from __future__ import annotations

from dataclasses import dataclass

from .config import AgentConfig
from .llm import LLMClient
from .mcp import MCPClientManager
from .state import StateManager
from .tools.registry import ToolRegistry
from .tools.invoker import ToolInvoker
from .policies import PolicyManager
from .guardrails import Guardrails


@dataclass(slots=True)
class AgentContext:
    config: AgentConfig
    state: StateManager
    llm: LLMClient
    tools: ToolRegistry
    tool_invoker: ToolInvoker
    mcp: MCPClientManager
    policies: PolicyManager
    guardrails: Guardrails
