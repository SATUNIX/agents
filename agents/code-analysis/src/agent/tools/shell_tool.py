"""Shell execution tool with guardrails."""

from __future__ import annotations

from typing import List

from pydantic import Field

from .base import LocalTool, ToolResult, ToolSchema


class ShellExecInput(ToolSchema):
    command: List[str] = Field(..., description="Command and arguments to run")
    cwd: str | None = Field(
        default=None, description="Optional working directory relative to workspace"
    )


class ShellExecTool(LocalTool):
    name = "workspace.shell_exec"
    description = "Execute a sandboxed shell command within the workspace"
    schema = ShellExecInput

    def _execute(self, params: ShellExecInput) -> ToolResult:
        target_cwd = self._within_workspace(params.cwd or ".")
        completed = self._run_shell(params.command, cwd=target_cwd)
        return ToolResult(
            status="ok",
            details={
                "command": params.command,
                "cwd": str(target_cwd),
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            },
        )
