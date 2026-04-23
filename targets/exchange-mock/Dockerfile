# Leviathan Sparring Lab — exchange-mock — Mock Autodiscover/EWS endpoints + weak auth (exchange chain)
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Exchange mock — Autodiscover/EWS weak auth, NTLM probe, OWA cred harvest surface"

RUN pip install --no-cache-dir flask

COPY app.py /app/app.py
WORKDIR /app

EXPOSE 80 443

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost/health')" || exit 1

CMD ["python", "app.py"]
