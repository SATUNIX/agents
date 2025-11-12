# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 agent

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN pip install --no-cache-dir -e .

RUN chown -R agent:agent /app

USER agent

ENV AGENT_WORKSPACE=/workspace \
    AGENT_STATE_DIR=/state \
    AGENT_TOOLS_DIR=/tools \
    OPENAI_API_KEY=sk-fake \
    OPENAI_BASE_URL=http://host.docker.internal:1234/v1 \
    AGENT_MODEL=gpt-4o-mini \
    AGENT_START_GOAL="Describe workspace status"

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "agent", "run"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -m agent --help > /dev/null 2>&1 || exit 1
