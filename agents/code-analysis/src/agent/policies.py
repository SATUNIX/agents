"""Policy-as-code loader and enforcement."""

from __future__ import annotations

import os
import signal
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class PolicyViolation(RuntimeError):
    """Raised when a policy constraint is violated."""


def _load_yaml(path: Path) -> Dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@dataclass(slots=True)
class PolicyManager:
    directory: Path

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._tool_calls = 0
        self._token_usage = 0
        self.tools_policy: Dict = {}
        self.network_policy: Dict = {}
        self.paths_policy: Dict = {}
        self.reload()

    def reload(self) -> None:
        with self._lock:
            self.tools_policy = _load_yaml(self.directory / "tools.yaml")
            self.network_policy = _load_yaml(self.directory / "network.yaml")
            self.paths_policy = _load_yaml(self.directory / "paths.yaml")
            self._tool_calls = 0
            self._token_usage = 0

    def validate(self) -> Dict[str, bool]:
        results = {}
        for name, data in (
            ("tools.yaml", self.tools_policy),
            ("network.yaml", self.network_policy),
            ("paths.yaml", self.paths_policy),
        ):
            results[name] = bool(data)
        return results

    # Budget enforcement -------------------------------------------------
    def authorize_tool(self, tool_name: str) -> None:
        with self._lock:
            self._tool_calls += 1
            limit = self._budget("max_tool_calls")
            if limit and self._tool_calls > limit:
                raise PolicyViolation(
                    f"Tool budget exceeded ({self._tool_calls}/{limit}) while calling {tool_name}"
                )
            allowed_tools = self.tools_policy.get("agents", {}).get("executor", {}).get(
                "allowed_tools", []
            )
            if allowed_tools and tool_name not in allowed_tools:
                raise PolicyViolation(f"Tool {tool_name} not permitted by policy")

    def record_tokens(self, tokens: int) -> None:
        with self._lock:
            self._token_usage += tokens
            limit = self._budget("max_tokens")
            if limit and self._token_usage > limit:
                raise PolicyViolation(
                    f"Token budget exceeded ({self._token_usage}/{limit})"
                )

    def _budget(self, key: str) -> Optional[int]:
        budgets = self.tools_policy.get("budgets", {})
        return budgets.get(key) or self.tools_policy.get("defaults", {}).get(key)

    # Accessors ----------------------------------------------------------
    def allowed_commands(self) -> List[str]:
        override = os.getenv("AGENT_ALLOWED_COMMANDS")
        if override:
            return [cmd.strip() for cmd in override.split(",") if cmd.strip()]
        defaults = self.tools_policy.get("defaults", {})
        return defaults.get(
            "allowed_commands",
            ["ls", "cat", "python", "pytest", "rg", "git", "git status"],
        )

    def allow_network(self) -> bool:
        if "allow_net" in self.network_policy:
            return bool(self.network_policy.get("allow_net"))
        return True

    def allowed_hosts(self) -> List[str]:
        return self.network_policy.get("allowed_hosts", [])

    def blocked_hosts(self) -> List[str]:
        return self.network_policy.get("blocked_hosts", [])

    def allowed_globs(self) -> List[str]:
        return self.paths_policy.get("allowed_globs", [])

    def blocked_globs(self) -> List[str]:
        return self.paths_policy.get("blocked_globs", [])

    def pid_file(self) -> Path:
        return (Path(os.getenv("AGENT_STATE_DIR", ".")) / "agent.pid").resolve()

    def write_pid(self) -> None:
        self.pid_file().write_text(str(os.getpid()), encoding="utf-8")

    def send_reload_signal(self) -> None:
        pid_file = self.pid_file()
        if not pid_file.exists():
            raise RuntimeError("agent.pid not found; is the runtime running?")
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        os.kill(pid, signal.SIGHUP)
