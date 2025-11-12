"""Hosted MCP client bootstrap, invocation, and health reporting."""

from __future__ import annotations

import json
import subprocess
import time
import os
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional

import httpx
from websockets.sync.client import connect as ws_connect  # type: ignore

from .config import AgentConfig, MCPServerProfile
from .state import StateManager


class RateLimiter:
    """Simple per-minute rate limiter."""

    def __init__(self, limit_per_minute: Optional[int]) -> None:
        self.limit = limit_per_minute
        self.events: Deque[float] = deque()

    def allow(self) -> bool:
        if not self.limit:
            return True
        now = time.monotonic()
        window_start = now - 60
        while self.events and self.events[0] < window_start:
            self.events.popleft()
        if len(self.events) >= self.limit:
            return False
        self.events.append(now)
        return True


@dataclass(slots=True)
class EndpointState:
    last_health: str = "unknown"
    last_latency_ms: float | None = None
    last_error: str | None = None
    throttled: bool = False
    total_invocations: int = 0


@dataclass(slots=True)
class MCPClientManager:
    config: AgentConfig
    http_client_factory: Callable[[], httpx.Client] | None = None
    ws_connect_fn: Callable[..., any] = ws_connect
    state: StateManager | None = None
    _endpoints: Dict[str, MCPServerProfile] = field(init=False)
    _http_clients: Dict[str, httpx.Client] = field(init=False, default_factory=dict)
    _limiters: Dict[str, RateLimiter] = field(init=False, default_factory=dict)
    _states: Dict[str, EndpointState] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self._endpoints = {
            name: profile for name, profile in self.config.settings.mcp_endpoints.items() if profile.enabled
        }
        for name, profile in self._endpoints.items():
            self._limiters[name] = RateLimiter(profile.rate_limit_per_minute)
            self._states[name] = EndpointState()
        if self.http_client_factory is None:
            self.http_client_factory = lambda: httpx.Client(timeout=5)

    # ------------------------------------------------------------------
    def close(self) -> None:
        for client in self._http_clients.values():
            client.close()

    # ------------------------------------------------------------------
    def health_report(self) -> List[Dict[str, str | float | None]]:
        report: List[Dict[str, str | float | None]] = []
        for name, profile in self._endpoints.items():
            entry = self._check_health(name, profile)
            report.append(entry)
        return report

    def _check_health(self, name: str, profile: MCPServerProfile) -> Dict[str, str | float | None]:
        token_present = bool(self.config.resolve_secret(profile.auth_token_env))
        try:
            start = time.perf_counter()
            if profile.transport == "http" and profile.url:
                client = self._http_client(name)
                response = client.get(profile.url.rstrip("/") + "/health", headers=self._headers(profile))
                status = "ok" if response.status_code < 400 else f"http_{response.status_code}"
            elif profile.transport == "ws" and profile.url:
                data = json.dumps({"type": "health"})
                with self.ws_connect_fn(profile.url, additional_headers=self._ws_headers(profile)) as ws:
                    ws.send(data)
                    ws.recv()
                status = "ok"
            elif profile.transport == "stdio" and profile.command:
                payload = json.dumps({"action": "health"})
                subprocess.run(
                    [profile.command, *profile.args],
                    input=payload.encode(),
                    env=self._stdio_env(profile),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                status = "ok"
            else:
                status = "unsupported"
            latency_ms = (time.perf_counter() - start) * 1000
            self._states[name].last_health = status
            self._states[name].last_latency_ms = latency_ms
            self._states[name].last_error = None
        except Exception as exc:  # pragma: no cover - network failures
            status = "error"
            latency_ms = None
            self._states[name].last_health = "error"
            self._states[name].last_error = str(exc)

        return {
            "name": name,
            "transport": profile.transport,
            "url": profile.url or profile.command or "",
            "status": status,
            "latency_ms": self._states[name].last_latency_ms,
            "authenticated": "yes" if token_present else "no",
            "rate_limit_per_minute": profile.rate_limit_per_minute,
            "last_error": self._states[name].last_error,
            "throttled": self._states[name].throttled,
            "total_invocations": self._states[name].total_invocations,
        }

    # ------------------------------------------------------------------
    def invoke(self, endpoint: str, tool: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if endpoint not in self._endpoints:
            raise KeyError(f"Unknown MCP endpoint '{endpoint}'")
        profile = self._endpoints[endpoint]
        limiter = self._limiters[endpoint]
        if not limiter.allow():
            self._states[endpoint].throttled = True
            raise RuntimeError(f"Endpoint '{endpoint}' rate limit exceeded")
        self._states[endpoint].throttled = False
        self._states[endpoint].total_invocations += 1

        try:
            if profile.transport == "http" and profile.url:
                response = self._http_client(endpoint).post(
                    profile.url.rstrip("/") + "/invoke",
                    headers=self._headers(profile),
                    json={"tool": tool, "payload": payload},
                )
                response.raise_for_status()
                result = self._maybe_json(response.text)
            elif profile.transport == "ws" and profile.url:
                message = json.dumps({"type": "invoke", "tool": tool, "payload": payload})
                with self.ws_connect_fn(profile.url, additional_headers=self._ws_headers(profile)) as ws:
                    ws.send(message)
                    reply = ws.recv()
                result = self._maybe_json(reply)
            elif profile.transport == "stdio" and profile.command:
                input_payload = json.dumps({"tool": tool, "payload": payload})
                proc = subprocess.run(
                    [profile.command, *profile.args],
                    input=input_payload.encode(),
                    capture_output=True,
                    env=self._stdio_env(profile),
                    check=True,
                )
                result = self._maybe_json(proc.stdout.decode())
            else:
                raise RuntimeError(f"Unsupported transport for endpoint '{endpoint}'")
        except Exception as exc:
            self._log_event("mcp_invoke", endpoint, tool, payload, status="error", error=str(exc))
            raise

        self._log_event("mcp_invoke", endpoint, tool, payload, status="ok", result=result)
        return result

    # ------------------------------------------------------------------
    def dashboard_payload(self) -> Dict[str, Any]:
        return {
            "endpoints": self.health_report(),
        }

    def write_snapshot(self, path: Path) -> Path:
        payload = self.dashboard_payload()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    def _http_client(self, name: str) -> httpx.Client:
        client = self._http_clients.get(name)
        if client is None:
            client = self.http_client_factory()  # type: ignore[operator]
            self._http_clients[name] = client
        return client

    def _headers(self, profile: MCPServerProfile) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        token = self.config.resolve_secret(profile.auth_token_env)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _ws_headers(self, profile: MCPServerProfile) -> List[tuple[str, str]]:
        token = self.config.resolve_secret(profile.auth_token_env)
        headers: List[tuple[str, str]] = []
        if token:
            headers.append(("Authorization", f"Bearer {token}"))
        return headers

    def _stdio_env(self, profile: MCPServerProfile) -> Dict[str, str]:
        env = dict(**os.environ)
        token = self.config.resolve_secret(profile.auth_token_env)
        if token:
            env["MCP_TOKEN"] = token
        return env

    @staticmethod
    def _maybe_json(value: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {"raw": value}

    def _log_event(
        self,
        kind: str,
        endpoint: str,
        tool: str,
        payload: Dict[str, Any],
        status: str,
        result: Dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        if not self.state:
            return
        self.state.append_event(
            kind,
            {
                "endpoint": endpoint,
                "tool": tool,
                "payload": payload,
                "status": status,
                "result": result,
                "error": error,
            },
        )
