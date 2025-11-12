"""AgentRuntime wiring tests."""

from __future__ import annotations

import types

import pytest

import agent.runtime as runtime


class DummyOrchestrator:
    def __init__(self, context):
        self.context = context
        self.runs = []

    def run(self, goal: str) -> None:
        self.runs.append(goal)

    def resume(self) -> None:
        self.runs.append("resume")


def test_agent_runtime_run(monkeypatch, agent_config):
    monkeypatch.setattr(runtime.AgentConfig, "load", lambda: agent_config)
    monkeypatch.setattr(runtime, "LLMClient", lambda cfg: object())

    orch = DummyOrchestrator(None)

    def _orch_factory(ctx):
        orch.context = ctx
        return orch

    monkeypatch.setattr(runtime, "AgentOrchestrator", _orch_factory)

    rt = runtime.AgentRuntime(run_id="testrun")
    rt.run("demo goal")
    rt.resume()

    assert orch.runs[0] == "demo goal"
    assert "resume" in orch.runs
    assert orch.context.config is agent_config
