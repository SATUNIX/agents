"""Command-line entrypoint for `python -m agent`."""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console

from .config import AgentConfig
from .runtime import AgentRuntime

app = typer.Typer(help="Run the OpenAI Agent SDK skeleton loop")
config_app = typer.Typer(help="Configuration utilities")
app.add_typer(config_app, name="config")

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


@config_app.command("view")
def config_view(pretty: bool = typer.Option(True, help="Pretty-print JSON output")) -> None:
    """Show the redacted runtime configuration."""

    config = AgentConfig.load()
    payload = config.public_dict()
    if pretty:
        console.print_json(data=payload)
    else:
        console.print(payload)


def main() -> None:  # pragma: no cover - Typer entry point
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
