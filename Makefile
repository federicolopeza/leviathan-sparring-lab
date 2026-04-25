# Leviathan Sparring Lab v2 — Makefile (lean)
#
# Targets v2 lifecycle. Legacy v1 makefile in legacy/Makefile.

SHELL := /bin/bash
.PHONY: help up down rotate harden smoke audit logs status clean

help:  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up:  ## bring up lab on VPS (requires .env.lab + VULTR_VPS_IP)
	@bash scripts/lab-up.sh

down:  ## snapshot + destroy VPS lifecycle (ephemeral pattern)
	@bash scripts/lab-down.sh

rotate:  ## swap GT — usage: make rotate STACK=dvwa
	@test -n "$(STACK)" || { echo "Usage: make rotate STACK=<name>"; exit 1; }
	@bash scripts/gt-rotate.sh $(STACK)

list-gt:  ## list available GTs in catalog
	@bash scripts/gt-rotate.sh --list

status-gt:  ## show current active GT
	@bash scripts/gt-rotate.sh --status

harden:  ## run harden.sh on VPS (idempotent)
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"cd /opt/levlab && sudo bash scripts/harden.sh --phase=all"

smoke:  ## run smoke tests
	@bash scripts/smoke.sh

audit:  ## lynis audit on VPS
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"sudo lynis audit system" | grep -E "Hardening index|warnings|suggestions"

waf-test:  ## verify CF WAF rules functional
	@bash scripts/waf-test.sh

logs:  ## tail container logs on VPS
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"cd /opt/levlab && sudo docker compose -f docker-compose.lean.yml logs -f --tail=50"

status:  ## show stack status on VPS
	@source .env.lab && ssh -i $$SSH_PRIVATE_KEY_PATH $$SSH_USER@$$VULTR_VPS_IP \
		"cd /opt/levlab && sudo docker compose -f docker-compose.lean.yml ps"

preflight:  ## verify Vultr preflight (region SCL, plan availability)
	@bash scripts/vultr-preflight.sh

cf-apply:  ## apply Cloudflare terraform (DNS + WAF + tunnel records)
	@cd terraform && terraform init && terraform apply

clean-bak:  ## clean .bak files from sed
	@find . -name '*.bak' -not -path './.git/*' -delete
