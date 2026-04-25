FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir uv

WORKDIR /app
COPY services/_shared /_shared
COPY services/api-gateway/pyproject.toml services/api-gateway/README.md ./
RUN uv pip install --system .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY services/api-gateway .

USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
