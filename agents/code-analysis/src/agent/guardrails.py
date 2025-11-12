"""Security guardrails for filesystem and subprocess actions."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .config import AgentConfig


class GuardrailViolation(RuntimeError):
    """Raised when a guardrail check fails."""


@dataclass(slots=True)
class Guardrails:
    config: AgentConfig
    allowed_commands: List[str] = None

    def __post_init__(self) -> None:
        if self.allowed_commands is None:
            self.allowed_commands = ["ls", "cat", "python", "pytest", "rg", "git status"]

    def ensure_workspace_path(self, path: Path) -> Path:
        normalized = (self.config.workspace / path).resolve()
        if self.config.workspace not in normalized.parents and normalized != self.config.workspace:
            raise GuardrailViolation(f"Path escape detected: {normalized}")
        return normalized

    def check_command(self, command: Iterable[str]) -> None:
        if not command:
            raise GuardrailViolation("Empty command")
        bin_name = command[0]
        if bin_name not in self.allowed_commands:
            raise GuardrailViolation(f"Command '{bin_name}' is not allowed")
        if not self.config.allow_net and any(token.startswith("http") for token in command):
            raise GuardrailViolation("Network call blocked by policy")

    def format_command(self, command: Iterable[str]) -> str:
        return " ".join(shlex.quote(part) for part in command)
