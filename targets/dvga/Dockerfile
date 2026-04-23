# Leviathan Sparring Lab — dvga — Damn Vulnerable GraphQL Application (introspection, authz, IDOR, depth abuse)
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ARG COMMIT_SHA=42b3c66
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WEB_HOST=0.0.0.0

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="DVGA — GraphQL introspection, authz bypass, over-fetching, IDOR resolvers, depth abuse"

RUN apt-get update -qq && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application.git /app \
    && git checkout ${COMMIT_SHA} || true

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5013

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5013/')" || exit 1

CMD ["python", "app.py"]
