# Leviathan Sparring Lab — oauth-lab — OAuth2 server (implicit flow, no PKCE, open redirect)
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_DEBUG=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="OAuth2 server — implicit flow, no PKCE, open redirect on authorize, weak JWKS, token leakage"

RUN pip install --no-cache-dir flask pyjwt cryptography

COPY app.py /app/app.py
WORKDIR /app

EXPOSE 5100

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5100/health')" || exit 1

CMD ["python", "app.py"]
