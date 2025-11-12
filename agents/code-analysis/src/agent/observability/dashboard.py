"""Simple FastAPI dashboard for metrics and checkpoints."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException

from ..policies import PolicyManager


STATE_DIR = Path(os.getenv("AGENT_STATE_DIR", "/state")).resolve()

app = FastAPI(title="Agent Observability", version="0.1.0")


def _safe_read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "state_dir": str(STATE_DIR)}


@app.get("/metrics")
def metrics() -> dict:
    return _safe_read_json(STATE_DIR / "metrics.json", {})


@app.get("/runs")
def runs() -> dict:
    checkpoints_dir = STATE_DIR / "checkpoints"
    run_ids = [p.name for p in checkpoints_dir.iterdir() if p.is_dir()] if checkpoints_dir.exists() else []
    return {"runs": sorted(run_ids)}


@app.get("/logs/{run_id}")
def logs(run_id: str, limit: int = 200) -> dict:
    log_path = STATE_DIR / "audit" / f"run-{run_id}.jsonl"
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Run log not found")
    lines = log_path.read_text(encoding="utf-8").splitlines()
    tail = lines[-limit:]
    events: List[dict] = []
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"run_id": run_id, "events": events}


@app.get("/checkpoints/{run_id}")
def checkpoint(run_id: str) -> dict:
    run_dir = STATE_DIR / "checkpoints" / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    data = {}
    for file in run_dir.glob("*.json"):
        try:
            data[file.stem] = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
    return {"run_id": run_id, "checkpoints": data}


@app.get("/mcp")
def mcp_endpoints() -> dict:
    return _safe_read_json(STATE_DIR / "tools" / "mcp_endpoints.json", {})


@app.post("/policies/reload")
def reload_policies() -> dict:
    manager = PolicyManager(Path(os.getenv("AGENT_POLICY_DIR", "policies")))
    manager.send_reload_signal()
    return {"status": "reloaded"}


def run_dashboard(host: str = "0.0.0.0", port: int = 7081) -> None:
    import uvicorn

    uvicorn.run("agent.observability.dashboard:app", host=host, port=port, reload=False)
