# Leviathan Sparring Lab — damn-vulnerable-ai-agent — DVAIA (tool-calling agent, bypass sanitization)
FROM python:3.11-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="DVAIA — AI agent with read_file/write_file/exec_shell tools that bypass sanitization"

RUN pip install --no-cache-dir fastapi uvicorn

COPY app.py /app/app.py
WORKDIR /app

EXPOSE 8002

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
