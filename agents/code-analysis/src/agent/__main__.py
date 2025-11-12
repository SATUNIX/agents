"""Command-line entrypoint for `python -m agent`."""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console

from .runtime import AgentRuntime

app = typer.Typer(help="Run the OpenAI Agent SDK skeleton loop")

console = Console()


def _default_goal() -> str:
    return os.getenv("AGENT_START_GOAL", "Describe workspace status")


@app.command()
def run(
    goal: Optional[str] = typer.Argument(
        None,
        help="Natural language goal for the agent (defaults to $AGENT_START_GOAL)",
    )
) -> None:
    """Execute the planner/executor/reviewer loop for a given goal."""

    target_goal = goal or _default_goal()
    console.rule("Agent Run")
    console.print(f"Goal: [bold]{target_goal}[/bold]")
    runtime = AgentRuntime()
    runtime.run(target_goal)
    console.print("[green]Run complete[/green]")


def main() -> None:  # pragma: no cover - Typer entry point
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
