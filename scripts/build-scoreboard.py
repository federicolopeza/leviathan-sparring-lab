#!/usr/bin/env python3
"""
build-scoreboard.py — Leviathan Sparring Lab
Reads findings.json + ground_truth.yml + defensive logs.
Writes 20-column scoreboard.csv per docs/09-metrics-scoring.md.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("[FAIL] pyyaml not installed. Run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


FIELDNAMES = [
    "run_id",
    "stack",
    "hostname",
    "chain",
    "ground_truth_id",
    "ground_truth_type",
    "ground_truth_value",
    "severity",
    "detected",
    "detected_at",
    "exploited",
    "exploited_at",
    "evidence_ref",
    "hash_chain_ok",
    "waf_interaction",
    "cloudflare_action",
    "modsec_action",
    "suricata_alert",
    "falco_alert",
    "ttf_seconds",
    "notes",
]


def load_json(path: Path) -> Any:
    if not path.exists():
        print(f"[WARN] {path} not found — returning empty list", file=sys.stderr)
        return []
    with path.open() as f:
        return json.load(f)


def load_yaml(path: Path) -> Any:
    if not path.exists():
        print(f"[WARN] {path} not found — returning empty dict", file=sys.stderr)
        return {}
    with path.open() as f:
        return yaml.safe_load(f)


def load_log_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text().splitlines()


def build_finding_index(findings: list[dict]) -> dict[str, dict]:
    """Index findings by ground_truth_id if present, else by finding_id."""
    idx: dict[str, dict] = {}
    for f in findings:
        gt_id = f.get("ground_truth_id") or f.get("gt_id")
        if gt_id:
            idx[gt_id] = f
        fid = f.get("finding_id") or f.get("id")
        if fid:
            idx[fid] = f
    return idx


def check_waf_logs(
    gt_id: str,
    cf_logs: list[dict],
    modsec_lines: list[str],
    suricata_lines: list[dict],
    falco_lines: list[dict],
) -> tuple[str, str, str, bool, bool]:
    """Return (waf_interaction, cf_action, modsec_action, suricata_hit, falco_hit)."""
    cf_action = "none"
    waf_interaction = "none"
    modsec_action = "modsec:pass"
    suricata_hit = False
    falco_hit = False

    for entry in cf_logs:
        if gt_id.lower() in json.dumps(entry).lower():
            cf_action = entry.get("action", "logged")
            waf_interaction = "challenged" if "challenge" in cf_action else cf_action
            break

    for line in modsec_lines:
        if gt_id.lower() in line.lower():
            modsec_action = "modsec:block" if "BLOCK" in line.upper() else "modsec:pass"
            break

    for entry in suricata_lines:
        if gt_id.lower() in json.dumps(entry).lower():
            suricata_hit = True
            break

    for entry in falco_lines:
        if gt_id.lower() in json.dumps(entry).lower():
            falco_hit = True
            break

    return waf_interaction, cf_action, modsec_action, suricata_hit, falco_hit


def extract_stacks(gt: dict) -> list[tuple[str, dict]]:
    """Yield (stack_name, gt_entry) from ground_truth.yml structure."""
    stacks = gt.get("stacks", {})
    results = []
    for stack_name, stack_data in stacks.items():
        expected = stack_data.get("expected", [])
        for entry in expected:
            results.append((stack_name, entry))
    return results


def build_row(
    run_id: str,
    stack: str,
    gt_entry: dict,
    finding: dict | None,
    waf_interaction: str,
    cf_action: str,
    modsec_action: str,
    suricata_hit: bool,
    falco_hit: bool,
    base_domain: str,
) -> dict:
    gt_id = gt_entry.get("id", "")
    detected = finding is not None
    exploited = finding.get("exploited", False) if finding else False
    detected_at = finding.get("detected_at", "") if finding else ""
    exploited_at = finding.get("exploited_at", "") if finding else ""
    evidence_ref = finding.get("evidence_ref", f"evidence/{stack}/{gt_id}.json") if finding else ""
    hash_chain_ok = str(finding.get("hash_chain_ok", False)).lower() if finding else "false"

    # TTF in seconds
    ttf = ""
    if finding and detected_at:
        import datetime
        try:
            t0_str = finding.get("engagement_start", "")
            if t0_str:
                t0 = datetime.datetime.fromisoformat(t0_str.replace("Z", "+00:00"))
                t1 = datetime.datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
                ttf = str(int((t1 - t0).total_seconds()))
        except Exception:
            ttf = ""

    # Hostname from stack name
    stack_hostname_map = {
        "wordpress-cve": f"wp.lab.{base_domain}",
        "drupal-cve": f"drupal.lab.{base_domain}",
        "joomla-cve": f"joomla.lab.{base_domain}",
        "juice-shop": f"juice.lab.{base_domain}",
        "dvwa": f"dvwa.lab.{base_domain}",
        "webgoat": f"webgoat.lab.{base_domain}",
        "mutillidae": f"mutillidae.lab.{base_domain}",
        "bwapp": f"bwapp.lab.{base_domain}",
        "django-goat": f"django.lab.{base_domain}",
        "railsgoat": f"rails.lab.{base_domain}",
        "spring-petclinic-vuln": f"spring.lab.{base_domain}",
        "vampi": f"vampi.lab.{base_domain}",
        "dvga": f"dvga.lab.{base_domain}",
        "crapi": f"crapi.lab.{base_domain}",
        "grpc-goat": f"grpc.lab.{base_domain}",
        "dotnet-goat": f"dotnet.lab.{base_domain}",
        "go-fuzz-svc": f"gofuzz.lab.{base_domain}",
        "keycloak-weak": f"keycloak.lab.{base_domain}",
        "oauth-lab": f"oauth.lab.{base_domain}",
        "saml-target": f"saml.lab.{base_domain}",
        "tenant-billing-api": f"tenant-billing.lab.{base_domain}",
        "jenkins-old": f"jenkins.lab.{base_domain}",
        "gitlab-ce-old": f"gitlab.lab.{base_domain}",
        "nexus-old": f"nexus.lab.{base_domain}",
        "sonarqube-old": f"sonar.lab.{base_domain}",
        "gitea-secrets": f"gitea.lab.{base_domain}",
        "minio-open": f"minio.lab.{base_domain}",
        "vault-dev-bad": f"vault.lab.{base_domain}",
        "localstack": f"aws.lab.{base_domain}",
        "mongo-open": f"data.lab.{base_domain}",
        "redis-open": f"data.lab.{base_domain}",
        "elastic-open": f"data.lab.{base_domain}",
        "postgres-open": f"data.lab.{base_domain}",
        "ad-budget": f"ad.lab.{base_domain}",
        "kube-goat-proxy": f"k8s.lab.{base_domain}",
        "mail-weak": f"mail.lab.{base_domain}",
        "exchange-mock": f"exchange.lab.{base_domain}",
        "iotgoat": f"iot.lab.{base_domain}",
        "promptme": f"ai.lab.{base_domain}",
        "dvaia": f"ai.lab.{base_domain}",
        "mobile-backend": f"mobile.lab.{base_domain}",
        "asterisk-weak": f"voip.lab.{base_domain}",
        "openplc-hmi": f"scada.lab.{base_domain}",
    }
    hostname = stack_hostname_map.get(stack, f"{stack}.lab.{base_domain}")

    return {
        "run_id": run_id,
        "stack": stack,
        "hostname": hostname,
        "chain": gt_entry.get("expected_chain", ""),
        "ground_truth_id": gt_id,
        "ground_truth_type": gt_entry.get("type", ""),
        "ground_truth_value": gt_entry.get("value", ""),
        "severity": gt_entry.get("severity", ""),
        "detected": str(detected).lower(),
        "detected_at": detected_at,
        "exploited": str(exploited).lower(),
        "exploited_at": exploited_at,
        "evidence_ref": evidence_ref,
        "hash_chain_ok": hash_chain_ok,
        "waf_interaction": waf_interaction,
        "cloudflare_action": cf_action,
        "modsec_action": modsec_action,
        "suricata_alert": str(suricata_hit).lower(),
        "falco_alert": str(falco_hit).lower(),
        "ttf_seconds": ttf,
        "notes": gt_entry.get("notes", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build 20-column scoreboard CSV from Leviathan findings + ground truth"
    )
    parser.add_argument("--findings", required=True, type=Path, help="findings.json path")
    parser.add_argument("--ground-truth", required=True, type=Path, help="ground_truth.yml path")
    parser.add_argument("--wazuh-alerts", type=Path, default=Path("/dev/null"))
    parser.add_argument("--cloudflare-logs", type=Path, default=Path("/dev/null"))
    parser.add_argument("--modsec-audit", type=Path, default=Path("/dev/null"))
    parser.add_argument("--suricata-eve", type=Path, default=Path("/dev/null"))
    parser.add_argument("--output", required=True, type=Path, help="scoreboard.csv output path")
    parser.add_argument("--run-id", default="", help="Run ID (overrides findings.json run_id)")
    parser.add_argument("--base-domain", default="example.com")
    args = parser.parse_args()

    # Load inputs
    findings_raw = load_json(args.findings)
    findings_list = findings_raw if isinstance(findings_raw, list) else findings_raw.get("findings", [])
    gt = load_yaml(args.ground_truth)
    cf_logs_raw = load_json(args.cloudflare_logs)
    cf_logs = cf_logs_raw if isinstance(cf_logs_raw, list) else cf_logs_raw.get("result", [])
    modsec_lines = load_log_lines(args.modsec_audit)

    suricata_lines: list[dict] = []
    if args.suricata_eve.exists():
        with args.suricata_eve.open() as f:
            for line in f:
                try:
                    suricata_lines.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    pass

    falco_lines: list[dict] = []
    # Falco logs may be in wazuh-alerts if piped through Wazuh
    wazuh_raw = load_json(args.wazuh_alerts)
    if isinstance(wazuh_raw, list):
        falco_lines = [e for e in wazuh_raw if e.get("source") == "falco"]

    run_id = args.run_id or (findings_list[0].get("run_id", "") if findings_list else "")
    finding_index = build_finding_index(findings_list)
    stacks = extract_stacks(gt)

    rows: list[dict] = []
    for stack, gt_entry in stacks:
        gt_id = gt_entry.get("id", "")
        finding = finding_index.get(gt_id)
        waf_interaction, cf_action, modsec_action, suricata_hit, falco_hit = check_waf_logs(
            gt_id, cf_logs, modsec_lines, suricata_lines, falco_lines
        )
        row = build_row(
            run_id=run_id,
            stack=stack,
            gt_entry=gt_entry,
            finding=finding,
            waf_interaction=waf_interaction,
            cf_action=cf_action,
            modsec_action=modsec_action,
            suricata_hit=suricata_hit,
            falco_hit=falco_hit,
            base_domain=args.base_domain,
        )
        rows.append(row)

    # Sort by severity (critical > high > medium > low) then by stack
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    rows.sort(key=lambda r: (severity_order.get(r["severity"], 9), r["stack"]))

    # Write CSV
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    detected = sum(1 for r in rows if r["detected"] == "true")
    exploited = sum(1 for r in rows if r["exploited"] == "true")
    coverage = detected / total if total > 0 else 0.0

    print(f"[OK] Scoreboard written: {args.output} ({total} rows)")
    print(f"     Coverage: {detected}/{total} = {coverage:.1%}")
    print(f"     Exploited: {exploited}/{total}")


if __name__ == "__main__":
    main()
