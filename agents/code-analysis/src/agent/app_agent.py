"""SDK-native agent definition and tool registration."""

from __future__ import annotations

from typing import List

from .config import AgentConfig
from .sdk_imports import Agent, HostedMCPTool
from .function_tools import build_function_tools


def build_agent(config: AgentConfig, policies, state) -> Agent:
    instructions = (
        "You are a code-focused agent operating strictly within the workspace. "
        "Respect policy prompts, summarize plans, and call the provided tools when appropriate."
    )

    hosted_tools: List[HostedMCPTool] = []
    for name, profile in config.settings.mcp_endpoints.items():
        hosted_tools.append(
            HostedMCPTool(
                name=name,
                transport=profile.transport,
                url=profile.url,
                command=profile.command,
                args=profile.args,
                auth_token_env=profile.auth_token_env,
            )
        )

    function_tools = build_function_tools(config, policies, state)

    return Agent(
        name="code-analysis-agent",
        instructions=instructions,
        model=config.agent_model,
        tools=[*function_tools, *hosted_tools],
    )
