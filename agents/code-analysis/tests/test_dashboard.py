"""Dashboard endpoint tests."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def dashboard_app(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "metrics.json").write_text(json.dumps({"events": 1}))
    audit_dir = state_dir / "audit"
    audit_dir.mkdir()
    (audit_dir / "run-foo.jsonl").write_text(json.dumps({"kind": "test", "payload": {}}) + "\n")
    checkpoints = state_dir / "checkpoints" / "foo"
    checkpoints.mkdir(parents=True)
    (checkpoints / "session.json").write_text(json.dumps({"goal": "demo"}))

    settings = tmp_path / "settings.yaml"
    settings.write_text(
        """
models: {}
agents: {}
tools: {}
policies: {}
mcp_endpoints: {}
""",
        encoding="utf-8",
    )

    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()

    monkeypatch.setenv("AGENT_STATE_DIR", str(state_dir))
    monkeypatch.setenv("AGENT_SETTINGS_PATH", str(settings))
    monkeypatch.setenv("AGENT_POLICY_DIR", str(policy_dir))
    monkeypatch.setenv("AGENT_WORKSPACE", str(tmp_path / "workspace"))
    monkeypatch.setenv("AGENT_TOOLS_DIR", str(tmp_path / "tools"))
    monkeypatch.setenv("AGENT_SECRETS_FILE", str(tmp_path / "secrets.env"))
    (tmp_path / "workspace").mkdir()
    (tmp_path / "tools").mkdir()
    (tmp_path / "secrets.env").write_text("", encoding="utf-8")

    from agent.observability import dashboard

    importlib.reload(dashboard)
    return dashboard.app


def test_dashboard_routes(dashboard_app):
    client = TestClient(dashboard_app)
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").json()["events"] == 1
    assert "foo" in client.get("/runs").json()["runs"]
    assert client.get("/logs/foo").status_code == 200
    assert client.get("/checkpoints/foo").status_code == 200
    assert client.get("/mcp").status_code == 200
    assert client.get("/mcp/health").status_code == 200
