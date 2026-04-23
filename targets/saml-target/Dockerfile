# Leviathan Sparring Lab — saml-target — SAML SP accepting unsigned assertions + XXE + weak audience
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_DEBUG=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="SAML SP — unsigned assertions accepted, ACS misconfig, XXE, weak audience check"

RUN pip install --no-cache-dir flask python3-saml lxml

COPY app.py     /app/app.py
COPY saml/      /app/saml/
WORKDIR /app

EXPOSE 5200

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5200/health')" || exit 1

CMD ["python", "app.py"]
