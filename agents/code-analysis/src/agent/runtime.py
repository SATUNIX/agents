"""Runtime wrapper that wires configuration into the official SDK Runner."""

from __future__ import annotations

import signal

from .config import AgentConfig
from .policies import PolicyManager
from .state import StateManager
from .mcp import MCPClientManager
from .sdk_imports import Runner
from .app_agent import build_agent


class AgentRuntime:
    """Thin wrapper around `Runner` with policy/telemetry plumbing."""

    def __init__(self, run_id: str | None = None) -> None:
        self.config = AgentConfig.load()
        self.config.write_snapshot()
        self.policies = PolicyManager(self.config.policy_dir)
        self.state = StateManager(self.config.state_dir, run_id=run_id, policy_manager=self.policies)
        self.mcp = MCPClientManager(self.config, state=self.state)
        self.mcp.write_snapshot(self.config.state_dir / "tools" / "mcp_endpoints.json")
        self.agent = build_agent(self.config, self.policies, self.state)
        self._runner = Runner(self.agent)
        self.policies.write_pid()
        signal.signal(signal.SIGHUP, self._handle_reload)

    def run(self, goal: str) -> None:
        self.policies.write_pid()
        self.state.append_event("runner_start", {"goal": goal})
        self._runner.run(goal)

    def resume(self, run_id: str | None = None) -> None:
        self.policies.write_pid()
        self.state.append_event("runner_resume", {"run_id": run_id})
        self._runner.resume(run_id=run_id)

    def _handle_reload(self, signum, frame):  # pragma: no cover - signal handler
        self.policies.reload()
