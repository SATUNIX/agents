"""Environment-driven configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AgentConfig:
    """Holds runtime configuration resolved from environment variables."""

    openai_base_url: str
    openai_api_key: str
    agent_model: str
    workspace: Path
    state_dir: Path
    tools_dir: Path
    allow_net: bool

    @classmethod
    def load(cls) -> "AgentConfig":
        """Create a config instance using environment variables and defaults."""

        workspace = Path(os.getenv("AGENT_WORKSPACE", "/workspace"))
        state_dir = Path(os.getenv("AGENT_STATE_DIR", "/state"))
        tools_dir = Path(os.getenv("AGENT_TOOLS_DIR", "/tools"))

        for directory in (workspace, state_dir, tools_dir):
            directory.mkdir(parents=True, exist_ok=True)

        return cls(
            openai_base_url=os.getenv("OPENAI_BASE_URL", "http://host.docker.internal:1234/v1"),
            openai_api_key=os.getenv("OPENAI_API_KEY", "sk-fake"),
            agent_model=os.getenv("AGENT_MODEL", "gpt-4o-mini"),
            workspace=workspace.resolve(),
            state_dir=state_dir.resolve(),
            tools_dir=tools_dir.resolve(),
            allow_net=os.getenv("ALLOW_NET", "false").lower() == "true",
        )

    def ensure_within_workspace(self, path: Path) -> Path:
        """Normalize `path` and ensure it lives under the workspace directory."""

        normalized = (self.workspace / path).resolve()
        if self.workspace not in normalized.parents and normalized != self.workspace:
            raise ValueError(f"Path {normalized} escapes workspace {self.workspace}")
        return normalized
