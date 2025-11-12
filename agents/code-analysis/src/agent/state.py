"""State and logging utilities for resumable runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class StateManager:
    """Persists JSONL events to the configured state directory."""

    def __init__(self, state_dir: Path, run_id: str | None = None) -> None:
        self.state_dir = state_dir
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self.log_path = self.state_dir / f"run-{self.run_id}.jsonl"
        self.audit_dir = self.state_dir / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def append_event(self, kind: str, payload: Dict[str, Any]) -> None:
        """Append a JSON line entry with a UTC timestamp."""

        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "payload": payload,
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")

    def write_audit(self, name: str, data: Dict[str, Any]) -> Path:
        """Persist structured audit artifacts under /state/audit."""

        path = self.audit_dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path
