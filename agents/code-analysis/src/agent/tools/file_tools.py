"""Filesystem read/write tools."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from .base import LocalTool, ToolContext, ToolResult, ToolSchema


class ReadFileInput(ToolSchema):
    path: str = Field(..., description="Relative path under workspace")


class WriteFileInput(ToolSchema):
    path: str = Field(..., description="Relative path under workspace")
    content: str = Field(..., description="UTF-8 text content")


class ReadFileTool(LocalTool):
    name = "workspace.read_file"
    description = "Read the contents of a file within the workspace"
    schema = ReadFileInput

    def _execute(self, params: ReadFileInput) -> ToolResult:
        file_path = self._within_workspace(params.path)
        data = file_path.read_text(encoding="utf-8")
        return ToolResult(status="ok", details={"path": str(file_path), "content": data})


class WriteFileTool(LocalTool):
    name = "workspace.write_file"
    description = "Write text to a file within the workspace"
    schema = WriteFileInput

    def _execute(self, params: WriteFileInput) -> ToolResult:
        file_path = self._within_workspace(params.path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(params.content, encoding="utf-8")
        return ToolResult(status="ok", details={"path": str(file_path), "bytes": len(params.content)})
