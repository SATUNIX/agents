"""Tests for the SDK-native agent builder."""

from __future__ import annotations

from agent import runtime
from agent.app_agent import build_agent
from agent.sdk_imports import Agent


def test_build_agent_returns_agent(agent_config):
    agent = build_agent(agent_config)
    assert isinstance(agent, Agent)
    assert agent.name == "code-analysis-agent"
    assert agent.tools  # includes workspace_status + hosted MCP entries (if any)


def test_runtime_uses_runner(monkeypatch, agent_config):
    monkeypatch.setattr(runtime.AgentConfig, "load", lambda: agent_config)
    events = []

    class DummyRunner:
        def __init__(self, agent):
            self.agent = agent

        def run(self, goal):
            events.append(("run", goal))

        def resume(self, run_id=None):
            events.append(("resume", run_id))

    monkeypatch.setattr(runtime, "Runner", DummyRunner)
    rt = runtime.AgentRuntime()
    rt.run("demo goal")
    rt.resume("run-1")
    assert events == [("run", "demo goal"), ("resume", "run-1")]
