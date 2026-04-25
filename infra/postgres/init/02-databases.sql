-- Melispy v3 database creation
-- Each service gets an isolated database; owned by melispy_app (V-T7-003 shared role)

CREATE DATABASE melispy_auth        WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_users       WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_orgs        WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_billing     WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_agents      WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_llm         WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_uploads     WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_webhooks    WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_search      WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_notifications WITH OWNER melispy_app ENCODING 'UTF8';
CREATE DATABASE melispy_admin       WITH OWNER melispy_app ENCODING 'UTF8';
