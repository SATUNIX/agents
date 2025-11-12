"""Guardrail tests."""

from __future__ import annotations

import pytest

from agent.guardrails import Guardrails, GuardrailViolation


def test_guardrails_block_network(agent_config) -> None:
    rails = Guardrails(agent_config)
    with pytest.raises(GuardrailViolation):
        rails.check_command(["curl", "http://example.com"])
