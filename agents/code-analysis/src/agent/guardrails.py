"""Security guardrails for filesystem and subprocess actions."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .config import AgentConfig
from .policies import PolicyManager, PolicyViolation


class GuardrailViolation(RuntimeError):
    """Raised when a guardrail check fails."""


@dataclass(slots=True)
class Guardrails:
    config: AgentConfig
    policies: PolicyManager

    def ensure_workspace_path(self, path: Path) -> Path:
        normalized = (self.config.workspace / path).resolve()
        if self.config.workspace not in normalized.parents and normalized != self.config.workspace:
            raise GuardrailViolation(f"Path escape detected: {normalized}")
        rel = normalized.relative_to(self.config.workspace)
        blocked = self._combined_blocked_globs()
        allowed = self._combined_allowed_globs()
        rel_str = str(rel)
        if blocked and any(fnmatch.fnmatch(rel_str, pattern) for pattern in blocked):
            raise GuardrailViolation(f"Path {rel_str} blocked by policy")
        if allowed and not any(fnmatch.fnmatch(rel_str, pattern) for pattern in allowed):
            raise GuardrailViolation(f"Path {rel_str} not in allowed patterns")
        return normalized

    def check_command(self, command: Iterable[str]) -> None:
        cmd_list = list(command)
        if not cmd_list:
            raise GuardrailViolation("Empty command")
        bin_name = cmd_list[0]
        if not self._command_allowed(cmd_list):
            raise GuardrailViolation(f"Command '{bin_name}' is not allowed")
        if not self.policies.allow_network() and any(token.startswith("http") for token in cmd_list):
            raise GuardrailViolation("Network call blocked by policy")

    def refresh(self) -> None:
        # Placeholder for future stateful guardrails
        return

    def _combined_allowed_globs(self) -> List[str]:
        patterns = list(self.policies.allowed_globs())
        patterns += self._settings_globs("allowed")
        return [p for p in patterns if p]

    def _combined_blocked_globs(self) -> List[str]:
        patterns = list(self.policies.blocked_globs())
        patterns += self._settings_globs("denied")
        return [p for p in patterns if p]

    def _settings_globs(self, kind: str) -> List[str]:
        values: List[str] = []
        for tool in self.config.settings.tools.values():
            if kind == "allowed":
                values.extend(tool.allowed_globs or [])
            else:
                values.extend(tool.denied_globs or [])
        return values

    def _command_allowed(self, cmd_list: List[str]) -> bool:
        allowed_entries = self.policies.allowed_commands()
        for entry in allowed_entries:
            tokens = entry.split()
            if not tokens:
                continue
            if cmd_list[: len(tokens)] == tokens:
                return True
        # fallback to first token if multi-word not matched
        single_tokens = [entry.split()[0] for entry in allowed_entries if entry]
        return cmd_list[0] in single_tokens
