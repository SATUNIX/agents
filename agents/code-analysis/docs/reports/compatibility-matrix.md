# Compatibility Matrix

| Backend | Mode | Detection | Smoke Test | Notes |
| --- | --- | --- | --- | --- |
| OpenAI Responses API | `AGENT_FORCE_CHAT_COMPLETIONS` unset | `AgentsGateway._supports_responses_api` → True | `scripts/smoke_test.py` outputs "Responses mode ready" | Tool-calls routed through Responses API with automatic local tool invocations, retries, and policy-safe logging. |
| LM Studio / Chat-only | `AGENT_FORCE_CHAT_COMPLETIONS=true` or missing Responses endpoints | `_supports_responses_api` → False | `scripts/smoke_test.py` prints fallback message | Uses chat completions with policy prompts; executor relies on local context only. |

Run the automated check:

```bash
python scripts/smoke_test.py
```

For CI automation, the nightly workflow executes both modes (default + `AGENT_FORCE_CHAT_COMPLETIONS=true`) to ensure parity.
