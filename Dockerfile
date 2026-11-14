# Образ только для агента: правила + LLM-слой + HTTP API. Данные и ноутбуки — локально через uv.
FROM python:3.11-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.9.10 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-default-groups --no-install-project

COPY agent/src agent/src
WORKDIR /app/agent
RUN useradd --create-home reviewer
USER reviewer
EXPOSE 8000
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]


# Тот же образ + pytest и тесты/примеры: docker compose run --rm agent-check
FROM runtime AS test
USER root
WORKDIR /app
RUN uv sync --frozen --no-default-groups --group dev --no-install-project
COPY agent/tests agent/tests
COPY agent/examples agent/examples
WORKDIR /app/agent
USER reviewer
CMD ["pytest", "-q", "-p", "no:cacheprovider", "tests"]
