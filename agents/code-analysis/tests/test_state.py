"""State manager tests."""

from __future__ import annotations

from agent.state import StateManager


def test_state_manager_records(tmp_path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    manager = StateManager(state_dir, run_id="test")

    manager.append_event("test_event", {"value": 1})
    manager.record_tool_metric("workspace.read", duration=0.1, success=True)
    manager.record_tokens("planner", 10, 5)

    log_path = state_dir / "audit" / "run-test.jsonl"
    assert log_path.exists()
    assert "test_event" in log_path.read_text(encoding="utf-8")

    metrics_path = state_dir / "metrics.json"
    data = metrics_path.read_text(encoding="utf-8")
    assert "workspace.read" in data
    assert "planner" in data

    manager.save_checkpoint("session", {"goal": "demo"})
    restored = manager.load_checkpoint("session")
    assert restored == {"goal": "demo"}
