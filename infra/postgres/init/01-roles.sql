-- INTENTIONAL VULN: V-T7-003 (shared role across services)
-- Single melispy_app role used by ALL microservices — compromise of one service = full DB access

CREATE ROLE melispy_app WITH LOGIN PASSWORD 'changeme';
