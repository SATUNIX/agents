"""Bridge to the OpenAI Agents SDK with tool + fallback support."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Iterable, List, Optional

from openai import OpenAI
from openai import APIError  # type: ignore[attr-defined]
from openai import RateLimitError  # type: ignore[attr-defined]

from .config import AgentConfig, AgentProfile, ToolProfile
from .tools.invoker import ToolInvoker
from .tools.registry import ToolRegistry
from .tools.base import ToolError
from .state import StateManager
from .policies import PolicyViolation


class AgentsGateway:
    """Creates and runs agents defined in the YAML settings registry."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: ToolRegistry | None = None,
        tool_invoker: ToolInvoker | None = None,
        state: StateManager | None = None,
        max_tool_iterations: int = 3,
        max_retries: int = 3,
        force_chat: bool | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self.config = config
        self._client = client or OpenAI(
            api_key=config.openai_api_key.get_secret_value(),
            base_url=config.openai_base_url,
        )
        self._agent_cache: Dict[str, str] = {}
        self.tool_registry = tool_registry
        self.tool_invoker = tool_invoker
        self.state = state
        self._max_tool_iterations = max_tool_iterations
        self._max_retries = max_retries
        self._force_chat = force_chat if force_chat is not None else os.getenv(
            "AGENT_FORCE_CHAT_COMPLETIONS"
        ) in {"1", "true", "True"}

    def run(self, agent_name: str, user_input: str, metadata: Dict[str, Any] | None = None) -> str:
        """Dispatch input through the Responses API or fall back to chat completions."""

        if self._supports_responses_api:
            return self._run_responses_flow(agent_name, user_input, metadata)
        return self._run_chat(agent_name, user_input)

    @property
    def _supports_responses_api(self) -> bool:
        if self._force_chat:
            return False
        return hasattr(self._client, "responses") and hasattr(self._client, "agents")

    def _run_responses_flow(
        self, agent_name: str, user_input: str, metadata: Dict[str, Any] | None
    ) -> str:
        if not self.tool_invoker:
            # Without tool invoker we cannot respond to function calls, so fall back
            return self._run_chat(agent_name, user_input)

        agent_id = self._ensure_agent(agent_name)
        response = self._request_with_retry(
            self._client.responses.create,
            agent_id=agent_id,
            input=[{"role": "user", "content": user_input}],
            metadata=metadata,
        )

        final_text: List[str] = []
        iterations = 0
        while iterations < self._max_tool_iterations:
            iterations += 1
            final_text.extend(self._extract_messages(response))
            tool_calls = self._extract_tool_calls(response)
            if not tool_calls:
                break
            tool_outputs = []
            for call in tool_calls:
                args = self._parse_arguments(call.get("arguments"))
                try:
                    result_payload = self.tool_invoker.invoke(call.get("name", ""), args)
                except (ToolError, PolicyViolation) as exc:
                    result_payload = {"error": str(exc)}
                tool_outputs.append(
                    {
                        "tool_call_id": call.get("id") or call.get("tool_call_id"),
                        "output": json.dumps(result_payload),
                    }
                )
            response = self._request_with_retry(
                self._client.responses.submit_tool_outputs,
                response_id=response.id,
                tool_outputs=tool_outputs,
            )

        text = "\n".join(final_text).strip()
        self._record_usage(agent_name, response)
        return text

    def _run_chat(self, agent_name: str, user_input: str) -> str:
        profile = self._get_profile(agent_name)
        response = self._request_with_retry(
            self._client.chat.completions.create,
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

    def _extract_messages(self, response: Any) -> List[str]:
        messages: List[str] = []
        output = getattr(response, "output", []) or []
        for item in output:
            item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
            if item_type != "message":
                continue
            message = getattr(item, "message", None) or item.get("message")
            if not message:
                continue
            content = getattr(message, "content", None) or message.get("content")
            if isinstance(content, list):
                for chunk in content:
                    if chunk.get("type") in {"output_text", "text"}:
                        messages.append(chunk.get("text", ""))
            elif isinstance(content, str):
                messages.append(content)
        return messages

    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        output = getattr(response, "output", []) or []
        calls: List[Dict[str, Any]] = []
        for item in output:
            item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
            if item_type != "tool_call":
                continue
            payload = getattr(item, "tool_call", None) or item.get("tool_call", {})
            function = payload.get("function", {})
            calls.append(
                {
                    "id": payload.get("id") or item.get("id"),
                    "name": function.get("name"),
                    "arguments": function.get("arguments") or function.get("input"),
                }
            )
        return calls

    def _parse_arguments(self, arguments: Optional[str]) -> Dict[str, Any]:
        if not arguments:
            return {}
        try:
            parsed = json.loads(arguments)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {"payload": arguments}

    def _request_with_retry(self, func, *args, **kwargs):
        delay = 1.0
        for attempt in range(self._max_retries):
            try:
                return func(*args, **kwargs)
            except (RateLimitError, APIError) as exc:
                if self.state:
                    self.state.record_error("backend")
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(delay)
                delay *= 2

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
