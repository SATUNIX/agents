"""SDK-native agent definition and tool registration."""

from __future__ import annotations

from typing import List

from .config import AgentConfig
from .sdk_imports import Agent, HostedMCPTool, function_tool


def build_agent(config: AgentConfig) -> Agent:
    instructions = (
        "You are a code-focused agent operating strictly within the workspace. "
        "Respect policy prompts, summarize plans, and call the provided tools when appropriate."
    )

    @function_tool(name="workspace_status", description="Describe workspace constraints")
    def workspace_status() -> str:
        policy_path = config.policy_dir
        return (
            "Workspace root: "
            + str(config.workspace)
            + ", policy bundle: "
            + str(policy_path)
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

    return Agent(
        name="code-analysis-agent",
        instructions=instructions,
        model=config.agent_model,
        tools=[workspace_status, *hosted_tools],
    )
