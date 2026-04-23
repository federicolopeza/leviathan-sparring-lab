# api-services

Backend API services for the Leviathan Inc platform.

Rails-based REST API connected to PostgreSQL. Authenticated via Keycloak OAuth2.

## Stack

- Ruby 3.2 / Rails 7
- PostgreSQL (production)
- Keycloak client credentials flow

## Setup

```bash
bundle install
rails db:migrate
rails server
```

## Configuration

See `config/database.yml` for database credentials and `src/auth/keys.json` for
Keycloak client configuration.
