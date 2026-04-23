# Leviathan Sparring Lab — vampi — VAmPI (OWASP API Top 10: BOLA, data exposure, rate limit, token weak)
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ARG COMMIT_SHA=71d70c8
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="VAmPI — OWASP API Top 10, BOLA, data exposure, rate limit bypass, weak tokens"

RUN apt-get update -qq && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/erev0s/VAmPI.git /app \
    && git checkout ${COMMIT_SHA} || true

RUN pip install --no-cache-dir -r requirements.txt

# Enable vulnerable mode (no rate limiting, debug on)
ENV VULNERABLE=1 \
    FLASK_DEBUG=1

EXPOSE 5000

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

CMD ["python", "app.py"]
