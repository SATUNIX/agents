"""Guardrail tests."""

from __future__ import annotations

import pytest

from pathlib import Path

from agent.guardrails import Guardrails, GuardrailViolation


def test_guardrails_block_network(agent_config, policy_manager) -> None:
    rails = Guardrails(agent_config, policy_manager)
    with pytest.raises(GuardrailViolation):
        rails.check_command(["curl", "http://example.com"])


def test_guardrails_multiword_command(agent_config, policy_manager) -> None:
    policy_manager.tools_policy.setdefault("defaults", {})["allowed_commands"] = [
        "git status",
        "ls",
    ]
    rails = Guardrails(agent_config, policy_manager)
    rails.check_command(["git", "status"])
    with pytest.raises(GuardrailViolation):
        rails.check_command(["git", "commit"])


def test_guardrails_paths(agent_config, policy_manager, tmp_path) -> None:
    rails = Guardrails(agent_config, policy_manager)
    allowed = rails.ensure_workspace_path(Path("notes.txt"))
    assert str(allowed).endswith("notes.txt")
    secret = agent_config.workspace / "secret" / "data.txt"
    secret.parent.mkdir(parents=True, exist_ok=True)
    with pytest.raises(GuardrailViolation):
        rails.ensure_workspace_path(secret.relative_to(agent_config.workspace))
