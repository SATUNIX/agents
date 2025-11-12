# QA Gap Analysis

| Area | Current Coverage | Gaps / Actions |
| --- | --- | --- |
| Config + Secrets | Pytest fixtures validate env loading, path enforcement, secret resolution. | Add negative tests for malformed YAML and missing secrets. |
| Tooling | Unit + integration tests now cover read/write, shell, guardrails, and MCP HTTP/STDIO flows. | Add repo-summary integration tests and WebSocket MCP coverage. |
| Planner/Executor/Reviewer | Deterministic SDK tests validate Responses + chat fallback; AgentRuntime run/resume covered. | Add full end-to-end test that executes planner→executor→reviewer with mocked completions writing to workspace. |
| Observability | FastAPI dashboard endpoints covered via TestClient; policy reload endpoint returns structured errors. | Add tests for `/policies/reload` success path once daemonized agent fixture exists. |
| CI Security | SBOM + Trivy + Cosign executed per release; coverage uploaded via CI. | Automate policy gating (fail release if critical CVEs or unsigned images) and publish coverage badge in README. |

Additional Actions:

1. Extend pytest suite with network fault simulations (mock 500s from LM Studio, MCP rate limits).
2. Expand nightly workflow to run chaos scenarios (LM Studio outage + MCP throttling) for >30 minutes.
3. Publish coverage badge in README once CI artifacts are exposed publicly.
