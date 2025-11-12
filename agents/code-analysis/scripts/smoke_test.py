#!/usr/bin/env python3
"""Compatibility smoke test for Responses vs Chat completion modes."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agent.sdk_imports import Runner


@dataclass
class ModeReport:
    force_chat: bool


def detect_mode() -> ModeReport:
    force_chat = os.getenv("AGENT_FORCE_CHAT_COMPLETIONS") in {"1", "true", "True"}
    return ModeReport(force_chat=force_chat)


def main() -> None:
    report = detect_mode()
    print("Force chat mode:", report.force_chat)
    print("Runner class detected:", Runner.__name__)
    if report.force_chat:
        print("ℹ️  Chat-completion fallback active. LM Studio compatibility expected.")
    else:
        print("🚀 Responses mode ready. Run `python -m agent run` to exercise tool calls.")


if __name__ == "__main__":
    main()
