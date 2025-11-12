"""Tool registration and provenance tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Type

from .base import LocalTool, ToolContext
from .file_tools import ReadFileTool, WriteFileTool
from .repo_summary import RepoSummaryTool
from .shell_tool import ShellExecTool


@dataclass(slots=True)
class ToolRegistry:
    context: ToolContext

    def __post_init__(self) -> None:
        self._tool_classes: Dict[str, Type[LocalTool]] = {
            cls.name: cls
            for cls in [ReadFileTool, WriteFileTool, ShellExecTool, RepoSummaryTool]
        }

    def names(self) -> List[str]:
        return sorted(self._tool_classes.keys())

    def create(self, name: str) -> LocalTool:
        try:
            tool_cls = self._tool_classes[name]
        except KeyError as exc:  # pragma: no cover
            raise KeyError(f"Unknown tool '{name}'") from exc
        return tool_cls(self.context)

    def describe(self) -> List[Dict[str, str]]:
        payload: List[Dict[str, str]] = []
        for name, tool_cls in self._tool_classes.items():
            payload.append({"name": name, "description": tool_cls.description})
        return payload

    def json_schema(self, name: str) -> Dict[str, object]:
        tool_cls = self._tool_classes[name]
        return tool_cls.schema.model_json_schema()

    def write_registry(self, path: Path) -> Path:
        payload = {
            name: {
                "description": tool_cls.description,
                "schema": tool_cls.schema.model_json_schema(),
            }
            for name, tool_cls in self._tool_classes.items()
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
