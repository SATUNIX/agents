"""Bridge to the OpenAI Agents SDK with graceful fallbacks."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from openai import OpenAI

from .config import AgentConfig, AgentProfile, ToolProfile
from .tools.invoker import ToolInvoker
from .tools.registry import ToolRegistry
from .state import StateManager


class AgentsGateway:
    """Creates and runs agents defined in the YAML settings registry."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: ToolRegistry | None = None,
        tool_invoker: ToolInvoker | None = None,
        state: StateManager | None = None,
    ) -> None:
        self.config = config
        self._client = OpenAI(
            api_key=config.openai_api_key.get_secret_value(),
            base_url=config.openai_base_url,
        )
        self._agent_cache: Dict[str, str] = {}
        self.tool_registry = tool_registry
        self.tool_invoker = tool_invoker
        self.state = state

    def run(self, agent_name: str, user_input: str, metadata: Dict[str, Any] | None = None) -> str:
        """Dispatch input through the official Agents API or fall back to chat completions."""

        if self._supports_agents_api:
            agent_id = self._ensure_agent(agent_name)
            response = self._client.responses.create(
                agent_id=agent_id,
                input=[{"role": "user", "content": user_input}],
                metadata=metadata,
            )
            text = self._extract_response_text(response)
            self._record_usage(agent_name, response)
            return text

        # Fallback for local LM Studio builds that only expose chat completions
        profile = self._get_profile(agent_name)
        response = self._client.chat.completions.create(
            model=profile.model,
            messages=[
                {
                    "role": "system",
                    "content": profile.description
                    or f"You are the {agent_name} role inside a multi-agent system.",
                },
                {"role": "user", "content": user_input},
            ],
            temperature=0.1,
        )
        text = (response.choices[0].message.content or "").strip()
        self._record_usage(agent_name, response)
        return text

    @property
    def _supports_agents_api(self) -> bool:
        return hasattr(self._client, "responses") and hasattr(self._client, "agents")

    def _ensure_agent(self, name: str) -> str:
        if name in self._agent_cache:
            return self._agent_cache[name]

        profile = self._get_profile(name)
        instructions = profile.description or f"You are the {name} agent in a multi-role workflow."
        instructions += self._policies_suffix(profile)
        tools_payload = self._build_tools(profile.tools)
        agent = self._client.agents.create(
            model=profile.model,
            instructions=instructions,
            tools=tools_payload or None,
            metadata={"policies": profile.policies},
        )
        self._agent_cache[name] = agent.id
        return agent.id

    def _get_profile(self, name: str) -> AgentProfile:
        try:
            return self.config.settings.agents[name]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise KeyError(f"Unknown agent profile '{name}' in settings") from exc

    def _policies_suffix(self, profile: AgentProfile) -> str:
        if not profile.policies:
            return ""
        statements: List[str] = []
        for policy_name in profile.policies:
            policy = self.config.settings.policies.get(policy_name)
            if not policy:
                continue
            if policy.description:
                statements.append(policy.description)
            statements.extend(policy.rules)
        if not statements:
            return ""
        joined = "\n".join(f"- {rule}" for rule in statements)
        return f"\nPolicy reminders:\n{joined}\n"

    def _build_tools(self, tool_names: Iterable[str]) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for tool_name in tool_names:
            profile: ToolProfile | None = self.config.settings.tools.get(tool_name)
            if not profile:
                continue
            tool_type = profile.type
            if tool_type in {"code_interpreter", "file_search", "web_search"}:
                payload.append({"type": tool_type})
                continue
            if tool_type == "local" and self.tool_registry and profile.handler:
                schema = self.tool_registry.json_schema(profile.handler)
                payload.append(
                    {
                        "type": "function",
                        "function": {
                            "name": profile.handler.replace(".", "_"),
                            "description": profile.description or profile.handler,
                            "parameters": schema,
                        },
                    }
                )
            else:
                payload.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool_name.replace(".", "_"),
                            "description": profile.description or tool_name,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "payload": {
                                        "type": "string",
                                        "description": "Generic payload",
                                    }
                                },
                                "required": ["payload"],
                            },
                        },
                    }
                )
        return payload

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        choices = getattr(response, "output", None) or getattr(response, "choices", None)
        if isinstance(choices, list):
            for choice in choices:
                message = getattr(choice, "message", None)
                if message and getattr(message, "content", None):
                    return str(message.content).strip()
        content = getattr(response, "output", response)
        return str(content)

    def _record_usage(self, agent_name: str, response: Any) -> None:
        if not self.state:
            return
        usage = getattr(response, "usage", None) or getattr(response, "response_metadata", {}).get("usage")
        if usage is None:
            return
        if isinstance(usage, dict):
            prompt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
            completion = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        else:
            prompt = getattr(usage, "prompt_tokens", getattr(usage, "input_tokens", 0))
            completion = getattr(usage, "completion_tokens", getattr(usage, "output_tokens", 0))
        self.state.record_tokens(agent_name, int(prompt or 0), int(completion or 0))
