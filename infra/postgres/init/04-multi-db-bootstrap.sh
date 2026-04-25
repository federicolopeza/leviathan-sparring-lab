#!/usr/bin/env bash
# Creates databases listed in POSTGRES_MULTIPLE_DATABASES (csv) if not already created by 01-databases.sql
# Runs as postgres superuser during container init
set -euo pipefail

if [ -z "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
  echo "POSTGRES_MULTIPLE_DATABASES not set, skipping"
  exit 0
fi

IFS=',' read -ra DATABASES <<< "$POSTGRES_MULTIPLE_DATABASES"
for db in "${DATABASES[@]}"; do
  db=$(echo "$db" | tr -d ' ')
  echo "Ensuring database: $db"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE $db OWNER melispy_app ENCODING ''UTF8'''
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
EOSQL
done
