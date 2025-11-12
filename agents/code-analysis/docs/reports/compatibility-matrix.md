# Compatibility Matrix

| Backend | Mode | Detection | Smoke Test | Notes |
| --- | --- | --- | --- | --- |
| OpenAI Responses API | `AGENT_FORCE_CHAT_COMPLETIONS` unset | Default Runner behavior (Responses enabled) | `scripts/smoke_test.py` outputs "Responses mode ready" | Tool-calls routed through Responses API with automatic local tool invocations, retries, and policy-safe logging. |
| LM Studio / Chat-only | `AGENT_FORCE_CHAT_COMPLETIONS=true` or missing Responses endpoints | Runner forced into fallback | `scripts/smoke_test.py` prints fallback message | Uses chat completions with policy prompts; executor relies on local context only. |

Run the automated check:

```bash
python scripts/smoke_test.py
```

For CI automation, the nightly workflow executes both modes (default + `AGENT_FORCE_CHAT_COMPLETIONS=true`) to ensure parity.
