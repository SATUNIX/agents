#!/usr/bin/env python3
"""Compatibility smoke test for Responses vs Chat completion modes."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agent.config import AgentConfig
from agent.sdk import AgentsGateway


@dataclass
class ModeReport:
    supports_responses: bool
    force_chat: bool


def detect_mode() -> ModeReport:
    cfg = AgentConfig.load()
    gateway = AgentsGateway(cfg, tool_registry=None, tool_invoker=None, state=None)
    return ModeReport(
        supports_responses=gateway._supports_responses_api,
        force_chat=os.getenv("AGENT_FORCE_CHAT_COMPLETIONS") in {"1", "true", "True"},
    )


def main() -> None:
    report = detect_mode()
    print("Responses API available:", report.supports_responses)
    print("Force chat mode:", report.force_chat)
    if report.supports_responses and not report.force_chat:
        print("🚀 Responses mode ready. Run `python -m agent run` to exercise tool calls.")
    else:
        print("ℹ️  Chat-completion fallback active. LM Studio compatibility expected.")


if __name__ == "__main__":
    main()
