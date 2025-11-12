"""Environment-driven configuration helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator


class AgentProfile(BaseModel):
    """Declarative description of an agent role."""

    model_config = ConfigDict(extra="allow")

    description: str | None = None
    model: str
    tools: list[str] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)


class ModelProfile(BaseModel):
    """Metadata about available models."""

    model_config = ConfigDict(extra="allow")

    provider: str
    temperature: float | None = None
    max_tokens: int | None = None


class ToolProfile(BaseModel):
    """Tool definition used by agents."""

    model_config = ConfigDict(extra="allow")

    type: str
    handler: str | None = None
    description: str | None = None
    allowed_globs: list[str] = Field(default_factory=list)
    denied_globs: list[str] = Field(default_factory=list)


class PolicyProfile(BaseModel):
    """Collection of guardrail rules."""

    model_config = ConfigDict(extra="allow")

    description: str | None = None
    rules: list[str] = Field(default_factory=list)


class SettingsRegistry(BaseModel):
    """Loaded YAML configuration describing agents/tools/models/policies."""

    model_config = ConfigDict(extra="ignore")

    agents: Dict[str, AgentProfile] = Field(default_factory=dict)
    models: Dict[str, ModelProfile] = Field(default_factory=dict)
    tools: Dict[str, ToolProfile] = Field(default_factory=dict)
    policies: Dict[str, PolicyProfile] = Field(default_factory=dict)
    mcp_endpoints: Dict[str, MCPServerProfile] = Field(default_factory=dict)

    @classmethod
    def from_path(cls, path: Path) -> "SettingsRegistry":
        if not path.exists():
            raise FileNotFoundError(f"Settings file not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(**data)


class AgentConfig(BaseModel):
    """Holds runtime configuration resolved from environment variables."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    openai_base_url: str
    openai_api_key: SecretStr
    agent_model: str
    workspace: Path
    state_dir: Path
    tools_dir: Path
    allow_net: bool = False
    settings_path: Path
    settings: SettingsRegistry
    secrets: Dict[str, SecretStr] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _ensure_directories(self) -> "AgentConfig":
        for directory in (self.workspace, self.state_dir, self.tools_dir):
            directory.mkdir(parents=True, exist_ok=True)
        return self

    @classmethod
    def load(cls) -> "AgentConfig":
        """Create a config instance using environment variables and defaults."""

        env = os.environ
        workspace = Path(env.get("AGENT_WORKSPACE", "/workspace")).expanduser().resolve()
        state_dir = Path(env.get("AGENT_STATE_DIR", "/state")).expanduser().resolve()
        tools_dir = Path(env.get("AGENT_TOOLS_DIR", "/tools")).expanduser().resolve()
        settings_path = Path(env.get("AGENT_SETTINGS_PATH", "config/settings.yaml")).expanduser().resolve()
        settings = SettingsRegistry.from_path(settings_path)
        secrets = cls._load_secrets(env.get("AGENT_SECRETS_FILE"))

        return cls(
            openai_base_url=env.get("OPENAI_BASE_URL", "http://host.docker.internal:1234/v1"),
            openai_api_key=SecretStr(env.get("OPENAI_API_KEY", "sk-fake")),
            agent_model=env.get("AGENT_MODEL", "gpt-4o-mini"),
            workspace=workspace,
            state_dir=state_dir,
            tools_dir=tools_dir,
            allow_net=env.get("ALLOW_NET", "false").lower() == "true",
            settings_path=settings_path,
            settings=settings,
            secrets=secrets,
        )

    @staticmethod
    def _load_secrets(secret_path_value: str | None) -> Dict[str, SecretStr]:
        if not secret_path_value:
            return {}
        secret_path = Path(secret_path_value).expanduser().resolve()
        if not secret_path.exists():
            return {}

        raw_text = secret_path.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError:
            data = None

        secrets: Dict[str, SecretStr] = {}
        items: Iterable[tuple[str, Any]] = []
        if isinstance(data, dict):
            items = list(data.items())
        else:
            parsed: list[tuple[str, str]] = []
            for line in raw_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                parsed.append((key.strip(), value.strip()))
            items = parsed

        for key, value in items:
            secrets[str(key)] = SecretStr(str(value))
        return secrets

    def ensure_within_workspace(self, path: Path) -> Path:
        """Normalize `path` and ensure it lives under the workspace directory."""

        normalized = (self.workspace / path).resolve()
        if self.workspace not in normalized.parents and normalized != self.workspace:
            raise ValueError(f"Path {normalized} escapes workspace {self.workspace}")
        return normalized

    def write_snapshot(self) -> Path:
        """Serialize the sanitized config to /state/config.json."""

        snapshot_path = self.state_dir / "config.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(self.public_dict(), indent=2), encoding="utf-8")
        return snapshot_path

    def public_dict(self) -> Dict[str, Any]:
        """Return a redacted, serialization-friendly payload."""

        return {
            "openai_base_url": self.openai_base_url,
            "agent_model": self.agent_model,
            "workspace": str(self.workspace),
            "state_dir": str(self.state_dir),
            "tools_dir": str(self.tools_dir),
            "allow_net": self.allow_net,
            "settings_path": str(self.settings_path),
            "settings": self.settings.model_dump(),
            "openai_api_key": self._redact_secret(self.openai_api_key),
            "secrets": {key: self._redact_secret(value) for key, value in self.secrets.items()},
        }

    @staticmethod
    def _redact_secret(secret: SecretStr | None) -> str:
        if secret is None:
            return ""
        value = secret.get_secret_value()
        if not value:
            return ""
        visible = value[-4:] if len(value) >= 4 else "***"
        return f"***{visible}"

    def get_secret(self, key: str) -> str | None:
        """Return a decrypted secret value if present."""

        secret = self.secrets.get(key)
        return secret.get_secret_value() if secret else None

    def resolve_secret(self, key: str | None) -> str | None:
        if not key:
            return None
        value = os.getenv(key)
        if value:
            return value
        return self.get_secret(key)
class MCPServerProfile(BaseModel):
    """Hosted MCP endpoint configuration."""

    model_config = ConfigDict(extra="allow")

    transport: str  # http, ws, stdio
    url: str | None = None
    command: str | None = None
    args: List[str] = Field(default_factory=list)
    auth_token_env: str | None = None
    rate_limit_per_minute: int | None = Field(default=None, ge=1)
    enabled: bool = True
