"""Shared context passed to role implementations."""

from __future__ import annotations

from dataclasses import dataclass

from .config import AgentConfig
from .llm import LLMClient
from .state import StateManager


@dataclass(slots=True)
class AgentContext:
    config: AgentConfig
    state: StateManager
    llm: LLMClient
