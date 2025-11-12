#!/usr/bin/env python3
"""Demonstrate executor-style file editing via local tools."""

from __future__ import annotations

import os
from pathlib import Path

from agent.runtime import AgentRuntime


def main() -> None:
    goal = os.getenv("DEMO_GOAL", "Describe workspace state")
    runtime = AgentRuntime(run_id=os.getenv("DEMO_RUN_ID"))
    runtime.run(goal)
    print("Submitted goal to Runner. Function-tool demo will be reintroduced once SDK tools land.")
if __name__ == "__main__":
    main()
