# Leviathan Sparring Lab — railsgoat — OWASP RailsGoat (mass assign, authz, SSRF, cmd exec, file upload)
FROM ruby:3.1-slim

ARG BUILD_COMMIT=unset
ARG COMMIT_SHA=5b22eea
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    RAILS_ENV=development \
    BUNDLE_WITHOUT="" \
    SECRET_KEY_BASE=lab-insecure-secret-key-railsgoat-000000

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="RailsGoat — mass assignment, authz bypass, SSRF, cmd exec, file upload"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        git nodejs libsqlite3-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/OWASP/railsgoat.git /app \
    && git checkout ${COMMIT_SHA} || true

RUN bundle install --without production

RUN bundle exec rake db:setup 2>/dev/null || bundle exec rake db:create db:migrate db:seed 2>/dev/null || true

EXPOSE 3000

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:3000/ || exit 1

CMD ["bundle", "exec", "rails", "server", "-b", "0.0.0.0"]
