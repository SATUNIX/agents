"""AgentsGateway compatibility tests."""

from __future__ import annotations

from types import SimpleNamespace

from agent.sdk import AgentsGateway
from agent.tools.registry import ToolRegistry
from agent.tools.base import ToolContext
from agent.guardrails import Guardrails
from agent.policies import PolicyManager
from agent.state import StateManager


class DummyToolInvoker:
    def __init__(self):
        self.calls = []

    def invoke(self, name, payload):
        self.calls.append((name, payload))
        return {"status": "ok", "details": payload}


class FakeResponses:
    def __init__(self):
        self._iteration = 0

    def create(self, **kwargs):
        return self._tool_call_response()

    def submit_tool_outputs(self, **kwargs):
        return self._final_response()

    def _tool_call_response(self):
        return SimpleNamespace(
            id="resp-1",
            output=[
                {
                    "type": "tool_call",
                    "tool_call": {
                        "id": "call-1",
                        "function": {
                            "name": "workspace.read_file",
                            "arguments": '{"path": "notes.txt"}',
                        },
                    },
                }
            ],
            usage={"input_tokens": 1, "output_tokens": 1},
        )

    def _final_response(self):
        return SimpleNamespace(
            id="resp-2",
            output=[
                {
                    "type": "message",
                    "message": {
                        "content": [
                            {"type": "output_text", "text": "Completed."},
                        ]
                    },
                }
            ],
            usage={"input_tokens": 1, "output_tokens": 1},
        )


class FakeAgents:
    def create(self, **kwargs):
        return SimpleNamespace(id="agent-1")


class FakeChatCompletions:
    def create(self, **kwargs):
        message = SimpleNamespace(content="Chat fallback")
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice], usage={"prompt_tokens": 1, "completion_tokens": 1})


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()
        self.agents = FakeAgents()
        self.chat = SimpleNamespace(completions=FakeChatCompletions())


def test_agents_gateway_responses_flow(agent_config, policy_manager, tmp_path) -> None:
    guardrails = Guardrails(agent_config, policy_manager)
    tool_context = ToolContext(agent_config, guardrails, policy_manager)
    registry = ToolRegistry(tool_context)
    invoker = DummyToolInvoker()
    state = StateManager(agent_config.state_dir, run_id="test", policy_manager=policy_manager)
    gateway = AgentsGateway(
        agent_config,
        tool_registry=registry,
        tool_invoker=invoker,
        state=state,
        client=FakeClient(),
        force_chat=False,
    )
    output = gateway.run("executor", "Use tools")
    assert "Completed" in output
    assert invoker.calls[0][0] == "workspace.read_file"


def test_agents_gateway_force_chat(monkeypatch, agent_config, policy_manager) -> None:
    monkeypatch.setenv("AGENT_FORCE_CHAT_COMPLETIONS", "true")
    state = StateManager(agent_config.state_dir, run_id="chat", policy_manager=policy_manager)
    gateway = AgentsGateway(
        agent_config,
        tool_registry=None,
        tool_invoker=None,
        state=state,
        client=FakeClient(),
    )
    output = gateway.run("planner", "Say hi")
    assert output == "Chat fallback"
