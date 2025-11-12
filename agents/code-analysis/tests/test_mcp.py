"""Tests for MCP connectivity."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
import pytest

from agent.config import AgentConfig
from agent.mcp import MCPClientManager


def _http_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path.endswith("/health"):
        return httpx.Response(200, json={"status": "ok"})
    if request.method == "POST" and request.url.path.endswith("/invoke"):
        payload = json.loads(request.content.decode())
        return httpx.Response(200, json={"echo": payload})
    return httpx.Response(404)


def _make_agent_config(tmp_path: Path, monkeypatch) -> AgentConfig:
    workspace = tmp_path / "workspace"
    state_dir = tmp_path / "state"
    tools_dir = tmp_path / "tools"
    policy_dir = tmp_path / "policies"
    for directory in (workspace, state_dir, tools_dir, policy_dir):
        directory.mkdir(parents=True, exist_ok=True)

    settings = tmp_path / "settings.yaml"
    script_path = tmp_path / "echo_stdio.py"
    settings.write_text(
        f"""
models:
  mock:
    provider: mock

agents:
  executor:
    model: mock
    tools: []

tools: {{}}
policies: {{}}
mcp_endpoints:
  http-test:
    transport: http
    url: https://mock.mcp
    auth_token_env: HTTP_TOKEN
    rate_limit_per_minute: 2
  stdio-test:
    transport: stdio
    command: '{sys.executable}'
    args: ['{script_path}']
    rate_limit_per_minute: 5
""",
        encoding="utf-8",
    )

    script_path.write_text(
        "import json,sys; data=json.loads(sys.stdin.read()); json.dump({'result': data}, sys.stdout)",
        encoding="utf-8",
    )

    monkeypatch.setenv("AGENT_WORKSPACE", str(workspace))
    monkeypatch.setenv("AGENT_STATE_DIR", str(state_dir))
    monkeypatch.setenv("AGENT_TOOLS_DIR", str(tools_dir))
    monkeypatch.setenv("AGENT_POLICY_DIR", str(policy_dir))
    monkeypatch.setenv("AGENT_SETTINGS_PATH", str(settings))
    monkeypatch.setenv("OPENAI_BASE_URL", "http://test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("HTTP_TOKEN", "secret")
    return AgentConfig.load()


def test_mcp_http_and_stdio(tmp_path, monkeypatch):
    config = _make_agent_config(tmp_path, monkeypatch)

    transport = httpx.MockTransport(_http_handler)

    manager = MCPClientManager(
        config,
        http_client_factory=lambda: httpx.Client(transport=transport),
    )

    health = manager.health_report()
    assert any(entry["name"] == "http-test" and entry["status"] == "ok" for entry in health)

    response = manager.invoke("http-test", "list", {"path": "notes.md"})
    assert response["echo"]["payload"]["path"] == "notes.md"

    stdio_response = manager.invoke("stdio-test", "echo", {"value": 1})
    assert stdio_response["result"]["payload"]["value"] == 1

    # Rate limit enforcement
    config.settings.mcp_endpoints["http-test"].rate_limit_per_minute = 1
    manager = MCPClientManager(
        config,
        http_client_factory=lambda: httpx.Client(transport=transport),
    )
    manager.invoke("http-test", "list", {})
    with pytest.raises(RuntimeError):
        manager.invoke("http-test", "list", {})
