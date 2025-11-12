"""Tests for agent configuration loading."""

from __future__ import annotations

import pytest

from agent.config import AgentConfig


def test_agent_config_loads(agent_config: AgentConfig) -> None:
    assert agent_config.workspace.exists()
    assert agent_config.settings.agents
    assert agent_config.settings.tools
    assert agent_config.agent_model == "gpt-4o-mini"


def test_ensure_within_workspace(agent_config: AgentConfig, tmp_path) -> None:
    inside = agent_config.ensure_within_workspace("notes.txt")
    assert str(agent_config.workspace) in str(inside)
    with pytest.raises(ValueError):
        agent_config.ensure_within_workspace("../outside.txt")
