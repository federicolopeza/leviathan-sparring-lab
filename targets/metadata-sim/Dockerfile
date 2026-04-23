# Leviathan Sparring Lab — metadata-sim — Simulated AWS IMDSv1 metadata service (SSRF target)
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Simulated AWS IMDSv1 — SSRF-to-metadata, short-lived creds, no IMDSv2 TTL enforcement"

RUN pip install --no-cache-dir flask

COPY app.py /app/app.py
WORKDIR /app

# Bind on port 80 — compose maps to 169.254.169.254:80 on the lab network
EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost/latest/meta-data/')" || exit 1

CMD ["python", "app.py"]
