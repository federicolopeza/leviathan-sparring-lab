# Leviathan Sparring Lab — djangogoat — DjangoGoat (debug mode, SQLi, authz bypass, secret leak)
FROM python:3.10-slim

ARG BUILD_COMMIT=unset
ARG COMMIT_SHA=6c6e3f5
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    DJANGO_DEBUG=True \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="DjangoGoat — debug exposure, secret leak, authz bypass, SQLi, template injection"

RUN apt-get update -qq && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/DjangoGoat/DjangoGoat.git /app \
    && git checkout ${COMMIT_SHA} || true

RUN pip install --no-cache-dir -r requirements.txt

# Seed weak secret key (intentional lab exposure)
ENV DJANGO_SECRET_KEY="lab-insecure-secret-key-do-not-use-in-prod-12345" \
    DATABASE_URL="sqlite:///db.sqlite3"

RUN python manage.py migrate --run-syncdb 2>/dev/null || true \
    && python manage.py loaddata fixtures/*.json 2>/dev/null || true

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
