"""Command-line entrypoint for `python -m agent`."""

from __future__ import annotations

import json
import os
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console

from .config import AgentConfig
from .runtime import AgentRuntime
from .state import StateManager
from .observability import run_dashboard
from .policies import PolicyManager
from .mcp import MCPClientManager

app = typer.Typer(help="Run the OpenAI Agent SDK skeleton loop")
config_app = typer.Typer(help="Configuration utilities")
tools_app = typer.Typer(help="Inspect and invoke local tools")
checkpoints_app = typer.Typer(help="Checkpoint utilities")
policies_app = typer.Typer(help="Policy-as-code controls")
mcp_app = typer.Typer(help="Hosted MCP utilities")
app.add_typer(config_app, name="config")
app.add_typer(tools_app, name="tools")
app.add_typer(checkpoints_app, name="checkpoints")
app.add_typer(policies_app, name="policies")
app.add_typer(mcp_app, name="mcp")

console = Console()


def _default_goal() -> str:
    return os.getenv("AGENT_START_GOAL", "Describe workspace status")


@app.command()
def run(
    goal: Optional[str] = typer.Argument(
        None,
        help="Natural language goal for the agent (defaults to $AGENT_START_GOAL)",
    ),
    run_id: Optional[str] = typer.Option(None, help="Reuse an existing run-id"),
) -> None:
    """Execute the planner/executor/reviewer loop for a given goal."""

    target_goal = goal or _default_goal()
    console.rule("Agent Run")
    console.print(f"Goal: [bold]{target_goal}[/bold]")
    runtime = AgentRuntime(run_id=run_id or os.getenv("AGENT_RUN_ID"))
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


@tools_app.command("list")
def tools_list() -> None:
    """List available local tools."""

    runtime = AgentRuntime()
    specs = runtime.context.tools.describe()
    console.print(specs)


@tools_app.command("run")
def tools_run(name: str, payload: str = typer.Option("{}", help="JSON payload")) -> None:
    """Invoke a local tool by name."""

    runtime = AgentRuntime()
    data = json.loads(payload)
    result = runtime.context.tool_invoker.invoke(name, data)
    console.print(result)


@checkpoints_app.command("list")
def checkpoints_list() -> None:
    """List checkpoint run IDs available under /state/checkpoints."""

    config = AgentConfig.load()
    runs = StateManager.list_available_runs(config.state_dir)
    console.print(runs or "No checkpoints recorded yet.")


@checkpoints_app.command("resume")
def checkpoints_resume(run_id: str = typer.Argument(..., help="Existing run identifier")) -> None:
    """Resume a previous run using stored checkpoints."""

    runtime = AgentRuntime(run_id=run_id)
    runtime.resume()
    console.print(f"[green]Resumed run {run_id}.[/green]")


@app.command()
def dashboard(host: str = "0.0.0.0", port: int = 7081) -> None:
    """Launch the FastAPI observability dashboard."""

    console.print(f"Starting dashboard on http://{host}:{port}")
    run_dashboard(host, port)


@policies_app.command("validate")
def policies_validate(policy_dir: str = typer.Option("policies", help="Policy directory")) -> None:
    manager = PolicyManager(Path(policy_dir))
    result = manager.validate()
    console.print(result)


@policies_app.command("reload")
def policies_reload() -> None:
    manager = PolicyManager(Path(os.getenv("AGENT_POLICY_DIR", "policies")))
    manager.send_reload_signal()
    console.print("[green]Sent SIGHUP to agent runtime[/green]")


@mcp_app.command("health")
def mcp_health() -> None:
    config = AgentConfig.load()
    manager = MCPClientManager(config)
    console.print(manager.health_report())


@mcp_app.command("invoke")
def mcp_invoke(
    endpoint: str = typer.Argument(..., help="MCP endpoint name"),
    tool: str = typer.Argument(..., help="Tool exposed by the endpoint"),
    payload: str = typer.Option("{}", help="JSON payload"),
) -> None:
    config = AgentConfig.load()
    manager = MCPClientManager(config)
    data = json.loads(payload)
    result = manager.invoke(endpoint, tool, data)
    console.print(result)


def main() -> None:  # pragma: no cover - Typer entry point
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
