#!/usr/bin/env python3
"""
reconcile.py — Leviathan Sparring Lab
findings x ground_truth reconciliation.
Outputs JSON per docs/09-metrics-scoring.md §Reconciliation output.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("[FAIL] pyyaml not installed. Run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> Any:
    if not path.exists():
        print(f"[WARN] {path} not found", file=sys.stderr)
        return []
    with path.open() as f:
        return json.load(f)


def load_yaml(path: Path) -> Any:
    if not path.exists():
        print(f"[WARN] {path} not found", file=sys.stderr)
        return {}
    with path.open() as f:
        return yaml.safe_load(f)


def extract_gt_entries(gt: dict) -> list[dict]:
    entries = []
    for stack_name, stack_data in gt.get("stacks", {}).items():
        for entry in stack_data.get("expected", []):
            entry["_stack"] = stack_name
            entries.append(entry)
    return entries


def build_finding_set(findings_raw: Any) -> set[str]:
    """Return set of ground_truth_ids covered by findings."""
    findings = findings_raw if isinstance(findings_raw, list) else findings_raw.get("findings", [])
    covered: set[str] = set()
    for f in findings:
        gt_id = f.get("ground_truth_id") or f.get("gt_id")
        if gt_id:
            covered.add(gt_id)
    return covered


def build_finding_index(findings_raw: Any) -> dict[str, dict]:
    findings = findings_raw if isinstance(findings_raw, list) else findings_raw.get("findings", [])
    idx: dict[str, dict] = {}
    for f in findings:
        gt_id = f.get("ground_truth_id") or f.get("gt_id")
        if gt_id:
            idx[gt_id] = f
        fid = f.get("finding_id") or f.get("id")
        if fid and fid not in idx:
            idx[fid] = f
    return idx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconcile Leviathan findings against ground truth"
    )
    parser.add_argument("--findings", required=True, type=Path)
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    findings_raw = load_json(args.findings)
    gt = load_yaml(args.ground_truth)

    gt_entries = extract_gt_entries(gt)
    covered = build_finding_set(findings_raw)
    finding_index = build_finding_index(findings_raw)

    # All findings without a GT match = potential FPs
    all_findings = (
        findings_raw if isinstance(findings_raw, list) else findings_raw.get("findings", [])
    )
    gt_ids = {e["id"] for e in gt_entries}
    false_positives: list[dict] = []
    for f in all_findings:
        gt_id = f.get("ground_truth_id") or f.get("gt_id")
        fid = f.get("finding_id") or f.get("id", "")
        if not gt_id or gt_id not in gt_ids:
            # Check for any defensive trace that might validate it
            has_trace = bool(f.get("evidence_ref") or f.get("log_ref"))
            if not has_trace:
                false_positives.append({
                    "finding_id": fid,
                    "severity": f.get("severity", ""),
                    "stack": f.get("stack", ""),
                    "reason": "no GT match + no defensive trace",
                })

    detected_gt = [e for e in gt_entries if e["id"] in covered]
    missed_gt = [e for e in gt_entries if e["id"] not in covered]

    # Chain bonus: count cross-stack chains detected
    cross_stack_entries = [e for e in gt_entries if "multi-stack chain" in e.get("notes", "")]
    cross_stack_detected = [e for e in cross_stack_entries if e["id"] in covered]

    total = len(gt_entries)
    n_detected = len(detected_gt)
    n_missed = len(missed_gt)
    coverage = n_detected / total if total > 0 else 0.0
    all_count = len(all_findings)
    precision = n_detected / all_count if all_count > 0 else 1.0

    result = {
        "total_gt": total,
        "detected_gt": n_detected,
        "missed_gt": [
            {
                "id": e["id"],
                "stack": e.get("_stack", ""),
                "severity": e.get("severity", ""),
                "type": e.get("type", ""),
                "reason": "not detected",
            }
            for e in missed_gt
        ],
        "false_positives": false_positives,
        "coverage": round(coverage, 3),
        "precision": round(precision, 3),
        "chain_bonus": len(cross_stack_detected),
        "chain_total": len(cross_stack_entries),
        "severity_breakdown": {
            sev: {
                "total": sum(1 for e in gt_entries if e.get("severity") == sev),
                "detected": sum(1 for e in detected_gt if e.get("severity") == sev),
            }
            for sev in ["critical", "high", "medium", "low"]
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as f:
        json.dump(result, f, indent=2)

    print(f"[OK] Reconciliation written: {args.output}")
    print(f"     Coverage: {n_detected}/{total} = {coverage:.1%}")
    print(f"     Precision proxy: {precision:.1%}")
    print(f"     Chain bonus: {len(cross_stack_detected)}/{len(cross_stack_entries)}")
    print(f"     False positives: {len(false_positives)}")


if __name__ == "__main__":
    main()
