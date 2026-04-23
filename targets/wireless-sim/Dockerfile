# Leviathan Sparring Lab — wireless-sim — Simulated captive portal + weak admin (wireless chain)
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Wireless captive portal sim — weak admin creds, credential harvest, RADIUS weak PSK"

RUN pip install --no-cache-dir flask

COPY app.py /app/app.py
WORKDIR /app

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost/health')" || exit 1

CMD ["python", "app.py"]
