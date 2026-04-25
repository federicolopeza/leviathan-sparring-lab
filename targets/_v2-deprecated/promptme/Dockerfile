# Leviathan Sparring Lab — promptme — LLM proxy with prompt injection + missing auth + insecure output
FROM python:3.11-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="LLM proxy — prompt injection, insecure output handling, missing auth, model DoS surface"

RUN pip install --no-cache-dir fastapi uvicorn

COPY app.py /app/app.py
WORKDIR /app

EXPOSE 8001

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
