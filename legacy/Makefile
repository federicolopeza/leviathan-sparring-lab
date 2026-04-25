SHELL := /bin/bash
include .env.lab
export

TF_DIR=terraform
ANSIBLE_DIR=ansible

.PHONY: preflight init apply ansible up smoke down destroy kill full teardown

preflight:
	@./scripts/vultr-preflight.sh

init: preflight
	cd $(TF_DIR) && terraform init -upgrade

apply:
	cd $(TF_DIR) && terraform apply /tmp/levlab.tfplan

ansible:
	@SERVER_IP=$$(cd $(TF_DIR) && terraform output -raw server_ipv4); \
	echo "lab ansible_host=$$SERVER_IP ansible_user=root" > $(ANSIBLE_DIR)/inventory.ini; \
	ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i $(ANSIBLE_DIR)/inventory.ini \
	  --private-key $$SSH_PRIVATE_KEY_PATH \
	  $(ANSIBLE_DIR)/site.yml

up:
	@SERVER_IP=$$(cd $(TF_DIR) && terraform output -raw server_ipv4); \
	scp -i $$SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=no .env.lab root@$$SERVER_IP:/opt/levlab/.env.lab; \
	ssh -i $$SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=no root@$$SERVER_IP \
	  'cd /opt/levlab && docker compose --env-file .env.lab up -d'

smoke:
	@./scripts/smoke.sh

down:
	@SERVER_IP=$$(cd $(TF_DIR) && terraform output -raw server_ipv4); \
	ssh -o StrictHostKeyChecking=no root@$$SERVER_IP \
	  'cd /opt/levlab && docker compose down -v --remove-orphans || true'

destroy:
	cd $(TF_DIR) && terraform destroy -auto-approve \
	  -var "vultr_api_key=$$VULTR_API_KEY" \
	  -var "cloudflare_api_token=$$CF_API_TOKEN" \
	  -var "cloudflare_zone_id=$$CF_ZONE_ID" \
	  -var "cloudflare_account_id=$$CF_ACCOUNT_ID" \
	  -var "base_domain=$$BASE_DOMAIN" \
	  -var "operator_public_ip=$$OPERATOR_PUBLIC_IP" \
	  -var "ssh_public_key=$$(cat $$SSH_PUBLIC_KEY_PATH)"

kill:
	@./scripts/kill.sh

full: init apply ansible up smoke
	@echo "[OK] Leviathan Sparring Lab deployed end-to-end. Kickoff permitted."

teardown:
	@./scripts/teardown.sh
