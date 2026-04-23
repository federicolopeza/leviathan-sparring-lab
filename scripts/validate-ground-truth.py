#!/usr/bin/env python3
"""
validate-ground-truth.py — Leviathan Sparring Lab
Validates ground_truth.yml schema per docs/05-ground-truth.md.
Checks: unique IDs, severity enum, expected_skill in known list,
expected_chain exists in arsenal chains list.
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[FAIL] pyyaml not installed. Run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)

VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_SKILLS = {
    "/pentest",
    "/api-audit",
    "/business-logic-audit",
    "/cloud-audit",
    "/container-audit",
    "/identity-attacks",
    "/supply-chain",
    "/source-audit",
    "/deep-hunter",
    "/web-hunter",
    "/waf-bypass",
}
VALID_TYPES = {
    "cve", "misconfig", "auth", "logic", "secret", "exposure",
    "injection", "idor", "xss", "xxe", "ssrf", "rce", "lateral",
    "privesc", "ai",
}
VALID_CONFIRMATION = {
    "response_body", "status_code", "auth_success", "exec_output",
    "dns_callback", "time_blind", "log_inspection", "db_write", "bucket_list",
}
KNOWN_CHAINS = {
    "generic_web.yaml", "api_rest.yaml", "api_graphql.yaml",
    "wordpress.yaml", "django.yaml", "rails.yaml", "spring.yaml",
    "node.yaml", "php.yaml", "go.yaml", "dotnet.yaml", "juice_shop.yaml",
    "exchange.yaml", "mail_server.yaml", "active_directory.yaml",
    "cloud_infrastructure.yaml", "cicd_supply_chain.yaml",
    "zero_day_research.yaml", "iot_embedded.yaml", "bug_bounty.yaml",
    "mobile_pentest.yaml", "wireless_pentest.yaml", "red_team_campaign.yaml",
    "saas_exploitation.yaml", "ai_ml_attacks.yaml", "voip_scada.yaml",
    "advanced_web.yaml", "social_engineering.yaml",
}


def validate(gt_path: Path) -> list[str]:
    errors: list[str] = []

    if not gt_path.exists():
        return [f"File not found: {gt_path}"]

    with gt_path.open() as f:
        gt = yaml.safe_load(f)

    if not isinstance(gt, dict) or "stacks" not in gt:
        return ["Root key 'stacks' missing"]

    seen_ids: set[str] = set()
    for stack_name, stack_data in gt.get("stacks", {}).items():
        if not isinstance(stack_data, dict):
            errors.append(f"{stack_name}: stack_data must be a dict")
            continue
        for i, entry in enumerate(stack_data.get("expected", [])):
            loc = f"{stack_name}[{i}]"
            gt_id = entry.get("id", "")

            # Unique ID
            if not gt_id:
                errors.append(f"{loc}: missing 'id' field")
            elif gt_id in seen_ids:
                errors.append(f"{loc}: duplicate ID '{gt_id}'")
            else:
                seen_ids.add(gt_id)

            # Severity enum
            sev = entry.get("severity", "")
            if sev not in VALID_SEVERITIES:
                errors.append(f"{loc} ({gt_id}): invalid severity '{sev}' — must be one of {VALID_SEVERITIES}")

            # Type enum
            typ = entry.get("type", "")
            if typ not in VALID_TYPES:
                errors.append(f"{loc} ({gt_id}): invalid type '{typ}' — must be one of {VALID_TYPES}")

            # expected_skill
            skill = entry.get("expected_skill", "")
            if skill and skill not in VALID_SKILLS:
                errors.append(f"{loc} ({gt_id}): unknown skill '{skill}' — valid: {VALID_SKILLS}")

            # expected_chain
            chain = entry.get("expected_chain", "")
            if chain:
                # Normalize: may include or omit .yaml
                chain_norm = chain if chain.endswith(".yaml") else chain + ".yaml"
                if chain_norm not in KNOWN_CHAINS:
                    errors.append(
                        f"{loc} ({gt_id}): unknown chain '{chain}' — "
                        f"valid chains: {sorted(KNOWN_CHAINS)}"
                    )

            # Cross-stack entries must have notes
            notes = entry.get("notes", "")
            if entry.get("type") == "lateral" and not notes:
                errors.append(f"{loc} ({gt_id}): lateral-movement GT entry missing 'notes' (cross-stack chain reference)")

            # confirmation_method
            confirm = entry.get("confirmation_method", "")
            if confirm and confirm not in VALID_CONFIRMATION:
                errors.append(f"{loc} ({gt_id}): invalid confirmation_method '{confirm}'")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate ground_truth.yml schema")
    parser.add_argument("ground_truth", type=Path, help="Path to ground_truth.yml")
    args = parser.parse_args()

    errors = validate(args.ground_truth)

    if errors:
        print(f"[FAIL] {len(errors)} validation error(s) found:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("[OK] ground_truth.yml valid — no schema errors found.")


if __name__ == "__main__":
    main()
