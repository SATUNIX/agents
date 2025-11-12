"""Tests for SDK function tools."""

from __future__ import annotations

from pathlib import Path

from agent.function_tools import build_function_tools
from agent.state import StateManager


def _tool_map(config, policy_manager, tmp_path):
    state = StateManager(tmp_path / "state", run_id="test", policy_manager=policy_manager)
    tools = build_function_tools(config, policy_manager, state)
    return {tool.__name__: tool}


def test_workspace_read_write(agent_config, policy_manager, tmp_path):
    tool_map = _tool_map(agent_config, policy_manager, tmp_path)
    writer = tool_map["workspace_write_file"]
    reader = tool_map["workspace_read_file"]
    writer(path="notes.txt", content="hello")
    content = reader(path="notes.txt")
    assert content == "hello"


def test_workspace_shell_exec(agent_config, policy_manager, tmp_path):
    tool_map = _tool_map(agent_config, policy_manager, tmp_path)
    shell_tool = tool_map["workspace_shell_exec"]
    output = shell_tool(command="ls", cwd=".")
    assert "stdout" in output


def test_workspace_repo_summary(agent_config, policy_manager, tmp_path):
    (agent_config.workspace / "a.md").write_text("doc", encoding="utf-8")
    tool_map = _tool_map(agent_config, policy_manager, tmp_path)
    summary = tool_map["workspace_repo_summary"]()
    assert summary["files_indexed"] >= 1
