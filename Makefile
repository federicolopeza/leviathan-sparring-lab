# Leviathan Sparring Lab — Melispy Inc. v3.0 Makefile

SHELL := /bin/bash
.PHONY: help engage triage redeploy score up down harden smoke audit logs status test clean

ENG  ?= $(error Usage: make engage/triage ENG=<engagement-id>)
V    ?= 3.0.0

help:  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ─── Engagement lifecycle ─────────────────────────────────────────────────────

engage:  ## start a new engagement — usage: make engage ENG=LEV-MELISPY-V3-001
	@echo "[engage] Starting engagement $(ENG)"
	@mkdir -p engagements/$(ENG)
	@cat > engagements/$(ENG)/ROE.md <<EOF
# Rules of Engagement — $(ENG)

- Target: Melispy Inc. v3.0 (app.melispy.com)
- Scope: All v3 services (auth, users, orgs, search, admin, notifications, billing, agents, llm)
- Out of scope: VPS host OS, Cloudflare infra, third-party OAuth providers
- Started: $$(date -u +%Y-%m-%dT%H:%M:%SZ)
- Loki dashboard: http://grafana.melispy.com/d/melispy-ssrf-recon
- VULN-CATALOG: $(shell git rev-parse --short HEAD) — 52 vulns across T1-T8
EOF
	@echo "[engage] ROE written to engagements/$(ENG)/ROE.md"
	@echo "[engage] Run Leviathan and pipe findings to engagements/$(ENG)/findings.json"
	@echo "[engage] Then: make triage ENG=$(ENG)"

triage:  ## triage findings against VULN-CATALOG — usage: make triage ENG=LEV-MELISPY-V3-001
	@echo "[triage] Processing engagement $(ENG)"
	@test -f engagements/$(ENG)/findings.json || { \
		echo "ERROR: engagements/$(ENG)/findings.json not found"; \
		echo "  Create it with: {\"findings\": [{\"vuln_id\": \"V-T2-001\", \"evidence\": \"...\"}]}"; \
		exit 1; \
	}
	@python3 scripts/triage.py \
		--engagement $(ENG) \
		--findings engagements/$(ENG)/findings.json \
		--catalog VULN-CATALOG.md \
		--output engagements/$(ENG)/triage-report.md
	@echo "[triage] Report: engagements/$(ENG)/triage-report.md"
	@echo "[triage] Score:"
	@grep "Tier.*score\|Total.*/" engagements/$(ENG)/triage-report.md || true

score:  ## compute engagement score — usage: make score ENG=LEV-MELISPY-V3-001
	@echo "[score] Scoring $(ENG)"
	@python3 scripts/triage.py \
		--engagement $(ENG) \
		--findings engagements/$(ENG)/findings.json \
		--catalog VULN-CATALOG.md \
		--score-only
	@echo "[score] Update ENGAGEMENT-LOG.md with result"

redeploy:  ## rebuild + redeploy services — usage: make redeploy V=3.0.1
	@echo "[redeploy] Deploying Melispy Inc. v$(V)"
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"cd /opt/levlab && git fetch origin && git checkout v$(V) && \
		 sudo docker compose -f infra/docker-compose.yml pull && \
		 sudo docker compose -f infra/docker-compose.yml up -d --build && \
		 sudo docker compose -f infra/docker-compose.yml ps"
	@echo "[redeploy] Running smoke tests..."
	@$(MAKE) smoke

# ─── Infra ────────────────────────────────────────────────────────────────────

up:  ## bring up local dev stack
	@docker compose -f infra/docker-compose.yml up -d
	@echo "[up] Stack running. API: http://localhost:8080"

down:  ## stop local dev stack
	@docker compose -f infra/docker-compose.yml down

certs:  ## generate internal CA + per-service mTLS certs
	@bash infra/ca/generate-certs.sh

harden:  ## run harden.sh on VPS (idempotent)
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"cd /opt/levlab && sudo bash scripts/harden.sh --phase=all"

smoke:  ## run smoke tests against deployed stack
	@bash scripts/smoke.sh

audit:  ## lynis host audit on VPS
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"sudo lynis audit system" | grep -E "Hardening index|warnings|suggestions"

logs:  ## tail container logs on VPS
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"cd /opt/levlab && sudo docker compose -f infra/docker-compose.yml logs -f --tail=50"

status:  ## show stack status on VPS
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"cd /opt/levlab && sudo docker compose -f infra/docker-compose.yml ps"

cf-apply:  ## apply Cloudflare terraform (DNS + WAF + tunnel)
	@cd terraform && terraform init && terraform apply

# ─── Tests ────────────────────────────────────────────────────────────────────

test:  ## run all service tests
	@echo "[test] Running all service tests..."
	@for svc in services/*/; do \
		if [ -f "$$svc/pyproject.toml" ]; then \
			echo "[test] $$svc..."; \
			(cd "$$svc" && python -m pytest tests/ -x -q --tb=short 2>&1 | tail -3) || true; \
		fi; \
	done
	@echo "[test] Done."

# ─── Maintenance ─────────────────────────────────────────────────────────────

clean:  ## remove Python caches (safe)
	@find services/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find services/ -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find services/ -name "*.pyc" -delete 2>/dev/null || true
	@echo "[clean] Done."

preflight:  ## verify Vultr preflight (region SCL, plan availability)
	@bash scripts/vultr-preflight.sh
