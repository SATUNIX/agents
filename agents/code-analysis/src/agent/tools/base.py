"""Base classes and utilities for local tool implementations."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field, ValidationError

from ..config import AgentConfig
from ..guardrails import Guardrails, GuardrailViolation


class ToolError(RuntimeError):
    """Raised when a tool execution fails."""


@dataclass(slots=True)
class ToolContext:
    config: AgentConfig


class ToolSchema(BaseModel):
    """Base schema for tool inputs."""

    class Config:
        extra = "forbid"


class ToolResult(BaseModel):
    """Represents a structured tool output."""

    status: str
    details: Dict[str, Any] = Field(default_factory=dict)


class LocalTool:
    """Base class for deterministic local tools."""

    name: str = "local_tool"
    description: str = ""
    schema: type[ToolSchema] = ToolSchema

    def __init__(self, context: ToolContext) -> None:
        self.context = context
        self.guardrails = Guardrails(context.config)

    def run(self, payload: Dict[str, Any]) -> ToolResult:
        try:
            params = self.schema.model_validate(payload)
        except ValidationError as exc:  # pragma: no cover - validation error path
            raise ToolError(str(exc)) from exc
        return self._execute(params)

    def _execute(self, params: ToolSchema) -> ToolResult:  # pragma: no cover - abstract
        raise NotImplementedError

    def _within_workspace(self, path: str | Path) -> Path:
        target = Path(path)
        return self.guardrails.ensure_workspace_path(target)

    def _run_shell(self, command: str, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        """Execute a shell command and return the completed process."""

        cwd = cwd or self.context.config.workspace
        cmd_list = command.split() if isinstance(command, str) else list(command)
        self.guardrails.check_command(cmd_list)
        proc = subprocess.run(
            cmd_list,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            raise ToolError(
                json.dumps(
                    {
                        "error": "shell_exec_failed",
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                        "code": proc.returncode,
                    }
                )
            )
        return proc
