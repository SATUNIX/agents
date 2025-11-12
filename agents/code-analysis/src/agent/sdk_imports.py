"""Helper that imports the OpenAI Agents SDK with graceful fallbacks for tests."""

from __future__ import annotations

try:  # pragma: no cover - exercised when dependency is present
    from openai.agents import Agent, Runner, function_tool, HostedMCPTool  # type: ignore
except Exception:  # pragma: no cover - fallback for local/test envs
    from ._sdk_stub import Agent, Runner, function_tool, HostedMCPTool  # noqa: F401

__all__ = ["Agent", "Runner", "function_tool", "HostedMCPTool"]
