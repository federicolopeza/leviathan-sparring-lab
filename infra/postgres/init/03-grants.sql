-- Grant melispy_app full access to all service databases
-- Runs after 02-databases.sql creates them

GRANT ALL PRIVILEGES ON DATABASE melispy_auth         TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_users        TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_orgs         TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_billing      TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_agents       TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_llm          TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_uploads      TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_webhooks     TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_search       TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_notifications TO melispy_app;
GRANT ALL PRIVILEGES ON DATABASE melispy_admin        TO melispy_app;
