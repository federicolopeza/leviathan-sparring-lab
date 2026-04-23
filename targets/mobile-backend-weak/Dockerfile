# Leviathan Sparring Lab — mobile-backend-weak — FastAPI mobile backend (hardcoded keys, weak JWT, IDOR)
FROM python:3.11-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Mobile backend — hardcoded API keys, weak JWT (alg=none accepted), IDOR on /user/<id>"

RUN pip install --no-cache-dir fastapi uvicorn pyjwt

COPY app.py /app/app.py
WORKDIR /app

EXPOSE 8003

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
