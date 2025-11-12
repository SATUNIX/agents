"""Tests for local tool implementations."""

from __future__ import annotations

import pytest

from agent.tools import (
    ToolContext,
    WriteFileTool,
    ReadFileTool,
    ShellExecTool,
    ToolError,
)


def test_read_write_tools(agent_config) -> None:
    context = ToolContext(agent_config)
    writer = WriteFileTool(context)
    reader = ReadFileTool(context)

    writer.run({"path": "hello.txt", "content": "hi"})
    result = reader.run({"path": "hello.txt"})
    assert result.details["content"] == "hi"


def test_shell_tool_guardrail(agent_config) -> None:
    context = ToolContext(agent_config)
    tool = ShellExecTool(context)
    with pytest.raises(ToolError):
        tool.run({"command": ["rm", "-rf", "/tmp"]})
