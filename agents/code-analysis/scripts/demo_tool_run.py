#!/usr/bin/env python3
"""Demonstrate executor-style file editing via local tools."""

from __future__ import annotations

import os
from pathlib import Path

from agent.runtime import AgentRuntime


def main() -> None:
    goal = os.getenv("DEMO_GOAL", "Demonstrate tool-backed execution")
    runtime = AgentRuntime(run_id=os.getenv("DEMO_RUN_ID"))
    ctx = runtime.context
    workspace_file = Path("demo.txt")
    ctx.tool_invoker.invoke(
        "workspace.write_file",
        {"path": str(workspace_file), "content": f"Generated via tool demo for goal: {goal}\n"},
    )
    result = ctx.tool_invoker.invoke("workspace.read_file", {"path": str(workspace_file)})
    print("File contents:\n", result["details"].get("content"))
    ctx.state.append_event(
        "demo_tool_run",
        {
            "goal": goal,
            "file": str(workspace_file),
            "result": result,
        },
    )
if __name__ == "__main__":
    main()
