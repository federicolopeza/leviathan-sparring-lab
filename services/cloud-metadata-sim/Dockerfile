FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
COPY services/cloud-metadata-sim/pyproject.toml services/cloud-metadata-sim/README.md ./
COPY services/cloud-metadata-sim/app ./app
RUN uv venv /app/.venv && uv pip install --python /app/.venv/bin/python .

FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system appuser && useradd --system --gid appuser --home-dir /app appuser

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY services/cloud-metadata-sim/app ./app

USER appuser
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
