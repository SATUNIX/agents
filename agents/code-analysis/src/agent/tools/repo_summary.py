"""Repository summarization tool."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List

from pydantic import Field

from .base import LocalTool, ToolResult, ToolSchema


class RepoSummaryInput(ToolSchema):
    max_files: int = Field(200, ge=1, le=2000)
    include_patterns: List[str] = Field(default_factory=lambda: ["**/*.py", "**/*.md"])


class RepoSummaryTool(LocalTool):
    name = "workspace.repo_summary"
    description = "Generate a quick summary of the repository tree"
    schema = RepoSummaryInput

    def _execute(self, params: RepoSummaryInput) -> ToolResult:
        workspace = self.context.config.workspace
        entries = list(workspace.rglob("*"))
        files: List[str] = []
        for entry in entries:
            if entry.is_file():
                rel = entry.relative_to(workspace)
                files.append(str(rel))
            if len(files) >= params.max_files:
                break
        digest = hashlib.sha256("\n".join(files).encode()).hexdigest()
        return ToolResult(
            status="ok",
            details={
                "files_indexed": len(files),
                "digest": digest[:16],
                "examples": files[:10],
            },
        )
