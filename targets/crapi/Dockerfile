# Leviathan Sparring Lab — crapi — Completely Ridiculous API (BOLA, mass assign, weak reset)
# NOTE: Full crAPI is a multi-container stack. This Dockerfile wraps only the web/identity
# service. The complete benchmark stack should use the upstream crAPI docker-compose:
#   https://github.com/OWASP/crAPI/blob/develop/deploy/docker/docker-compose.yml
# This scaffold image acts as a proxy/stub for integration testing until the full compose
# is wired. For the actual benchmark run, override with crAPI's own compose file.
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="crAPI stub — BOLA, mass assignment, auth flaws, logic, weak reset (full stack via upstream compose)"

RUN pip install --no-cache-dir flask requests

COPY crapi-stub.py /app/app.py

WORKDIR /app

EXPOSE 8888

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8888/health')" || exit 1

CMD ["python", "app.py"]
