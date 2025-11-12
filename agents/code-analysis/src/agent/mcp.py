"""Hosted MCP client bootstrap and health reporting."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .config import AgentConfig, MCPServerProfile


@dataclass(slots=True)
class MCPClientManager:
    config: AgentConfig

    def __post_init__(self) -> None:
        self._endpoints: Dict[str, MCPServerProfile] = self.config.settings.mcp_endpoints

    def endpoints(self) -> Dict[str, MCPServerProfile]:
        return self._endpoints

    def health_report(self) -> List[Dict[str, str]]:
        report: List[Dict[str, str]] = []
        for name, profile in self._endpoints.items():
            token_present = bool(self.config.resolve_secret(profile.auth_token_env))
            report.append(
                {
                    "name": name,
                    "transport": profile.transport,
                    "url": profile.url or profile.command or "unknown",
                    "rate_limit_per_minute": str(profile.rate_limit_per_minute or "unlimited"),
                    "authenticated": "yes" if token_present else "no",
                    "enabled": "yes" if profile.enabled else "no",
                }
            )
        return report

    def write_snapshot(self, path: Path) -> Path:
        payload = {
            "endpoints": self.health_report(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
