"""State, checkpoint, and metrics utilities."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .policies import PolicyManager


class MetricsRecorder:
    """Accumulates metrics and persists them as JSON."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8"))
        else:
            self.data = {
                "tools": {},
                "tokens": {},
                "errors": {},
                "events": 0,
            }

    def _persist(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def record_tool(self, name: str, duration: float, success: bool) -> None:
        entry = self.data.setdefault("tools", {}).setdefault(
            name, {"calls": 0, "errors": 0, "total_latency": 0.0}
        )
        entry["calls"] += 1
        entry["total_latency"] += duration
        if not success:
            entry["errors"] += 1
            self.data.setdefault("errors", {}).setdefault("tool", 0)
            self.data["errors"]["tool"] += 1
        self._persist()

    def record_tokens(self, actor: str, prompt: int, completion: int) -> None:
        actor_entry = self.data.setdefault("tokens", {}).setdefault(
            actor, {"prompt": 0, "completion": 0}
        )
        actor_entry["prompt"] += prompt
        actor_entry["completion"] += completion
        self._persist()

    def increment_error(self, kind: str) -> None:
        self.data.setdefault("errors", {}).setdefault(kind, 0)
        self.data["errors"][kind] += 1
        self._persist()

    def increment_event(self) -> None:
        self.data["events"] = self.data.get("events", 0) + 1
        self._persist()


class CheckpointStore:
    """Manages checkpoint files under /state/checkpoints/<run-id>."""

    def __init__(self, base_dir: Path, run_id: str) -> None:
        self.base_dir = base_dir
        self.run_id = run_id
        self.path = base_dir / run_id
        self.path.mkdir(parents=True, exist_ok=True)

    def save(self, stage: str, data: Dict[str, Any]) -> Path:
        file_path = self.path / f"{stage}.json"
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return file_path

    def load(self, stage: str) -> Optional[Dict[str, Any]]:
        file_path = self.path / f"{stage}.json"
        if not file_path.exists():
            return None
        return json.loads(file_path.read_text(encoding="utf-8"))

    def stages(self) -> List[str]:
        if not self.path.exists():
            return []
        return sorted(p.stem for p in self.path.glob("*.json"))

    @classmethod
    def list_runs(cls, base_dir: Path) -> List[str]:
        if not base_dir.exists():
            return []
        return sorted(p.name for p in base_dir.iterdir() if p.is_dir())


class StateManager:
    """Persists JSONL events, metrics, and checkpoints."""

    def __init__(self, state_dir: Path, run_id: str | None = None, policy_manager: PolicyManager | None = None) -> None:
        self.state_dir = state_dir
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self.audit_dir = self.state_dir / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.audit_dir / f"run-{self.run_id}.jsonl"
        self.metrics = MetricsRecorder(self.state_dir / "metrics.json")
        self.checkpoints = CheckpointStore(self.state_dir / "checkpoints", self.run_id)
        self.policy_manager = policy_manager

    def append_event(self, kind: str, payload: Dict[str, Any]) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "payload": payload,
        }
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
        self.metrics.increment_event()

    def write_audit(self, name: str, data: Dict[str, Any]) -> Path:
        path = self.audit_dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def save_checkpoint(self, stage: str, data: Dict[str, Any]) -> Path:
        return self.checkpoints.save(stage, data)

    def load_checkpoint(self, stage: str) -> Optional[Dict[str, Any]]:
        return self.checkpoints.load(stage)

    def checkpoint_stages(self) -> List[str]:
        return self.checkpoints.stages()

    @staticmethod
    def list_available_runs(state_dir: Path) -> List[str]:
        return CheckpointStore.list_runs(state_dir / "checkpoints")

    def record_tool_metric(self, name: str, duration: float, success: bool) -> None:
        self.metrics.record_tool(name, duration, success)

    def record_tokens(self, actor: str, prompt_tokens: int, completion_tokens: int) -> None:
        delta = prompt_tokens + completion_tokens
        if prompt_tokens or completion_tokens:
            self.metrics.record_tokens(actor, prompt_tokens, completion_tokens)
            if self.policy_manager and delta:
                self.policy_manager.record_tokens(delta)

    def record_error(self, kind: str) -> None:
        self.metrics.increment_error(kind)
