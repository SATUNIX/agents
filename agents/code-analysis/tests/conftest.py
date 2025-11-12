"""Shared pytest fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agent.config import AgentConfig


@pytest.fixture()
def config_env(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    state_dir = tmp_path / "state"
    tools_dir = tmp_path / "tools"
    for directory in (workspace, state_dir, tools_dir):
        directory.mkdir(parents=True, exist_ok=True)

    settings = tmp_path / "settings.yaml"
    settings.write_text(
        """
models:
  test-model:
    provider: lm-studio
    temperature: 0.1

tools:
  workspace.read_file:
    type: local
    handler: workspace.read_file
  workspace.write_file:
    type: local
    handler: workspace.write_file

policies:
  safety.default:
    description: none

agents:
  planner:
    model: test-model
    tools: [workspace.read_file]
  executor:
    model: test-model
    tools: [workspace.read_file, workspace.write_file]
  reviewer:
    model: test-model
    tools: [workspace.read_file]
""",
        encoding="utf-8",
    )

    secrets_file = tmp_path / "secrets.env"
    secrets_file.write_text("LM_TOKEN=abc123", encoding="utf-8")

    monkeypatch.setenv("AGENT_WORKSPACE", str(workspace))
    monkeypatch.setenv("AGENT_STATE_DIR", str(state_dir))
    monkeypatch.setenv("AGENT_TOOLS_DIR", str(tools_dir))
    monkeypatch.setenv("AGENT_SETTINGS_PATH", str(settings))
    monkeypatch.setenv("AGENT_SECRETS_FILE", str(secrets_file))
    monkeypatch.setenv("OPENAI_BASE_URL", "http://test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    return {
        "workspace": workspace,
        "state_dir": state_dir,
        "tools_dir": tools_dir,
    }


@pytest.fixture()
def agent_config(config_env) -> AgentConfig:
    return AgentConfig.load()
