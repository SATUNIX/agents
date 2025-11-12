# QA Gap Analysis

| Area | Current Coverage | Gaps / Actions |
| --- | --- | --- |
| Config + Secrets | Pytest fixtures validate env loading, path enforcement, and secret resolution. | Add negative tests for malformed YAML and missing secrets. |
| Tooling | Unit tests cover read/write, guardrail enforcement, and shell-blocking behavior. | Add integration tests for repo summary digests and MCP client health snapshots. |
| Planner/Executor/Reviewer | Checkpoint flow tested indirectly; need mock Agents SDK tests with deterministic completions. | Implement fixtures that simulate SDK responses and assert session persistence. |
| Observability | Dashboard endpoints exercised manually; not yet automated. | Add API tests using FastAPI test client for `/metrics`, `/logs`, `/checkpoints`. |
| CI Security | SBOM + Trivy + Cosign executed per release. | Automate policy gating (fail release if critical CVEs or unsigned images). |

Additional Actions:

1. Extend pytest suite with network fault simulations (mock 500s from LM Studio, MCP rate limits).
2. Add soak test workflow (`nightly` schedule) running `python -m agent run` for >30 min.
3. Integrate coverage reporting (e.g., `pytest --cov`) and publish badge in README.
