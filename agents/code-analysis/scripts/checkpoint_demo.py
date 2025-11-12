"""Demonstrate how to inspect and resume checkpoints."""

from __future__ import annotations

import os
from pathlib import Path

from agent.state import CheckpointStore


def main() -> None:
    state_dir = Path(os.getenv("AGENT_STATE_DIR", "./state")).resolve()
    checkpoints_root = state_dir / "checkpoints"
    runs = sorted((p.name for p in checkpoints_root.iterdir() if p.is_dir()), reverse=True) if checkpoints_root.exists() else []
    if not runs:
        print("No checkpoints available. Run `python -m agent run` first.")
        return
    latest = runs[0]
    store = CheckpointStore(checkpoints_root, latest)
    session = store.load("session")
    print(f"Latest run ID: {latest}")
    if not session:
        print("No session checkpoint found.")
        return
    print("Stored plan steps:")
    for idx, step in enumerate(session.get("plan_steps", []), start=1):
        print(f"  {idx}. {step}")
    print("\nResume with: python -m agent checkpoints resume", latest)


if __name__ == "__main__":
    main()
