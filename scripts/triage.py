#!/usr/bin/env python3
"""Triage script: map engagement findings to VULN-CATALOG.md and score by tier.

Usage:
    python scripts/triage.py --engagement LEV-MELISPY-V3-001 \\
        --findings engagements/LEV-MELISPY-V3-001/findings.json \\
        --catalog VULN-CATALOG.md \\
        --output engagements/LEV-MELISPY-V3-001/triage-report.md

    python scripts/triage.py --engagement LEV-MELISPY-V3-001 \\
        --findings engagements/LEV-MELISPY-V3-001/findings.json \\
        --catalog VULN-CATALOG.md --score-only

Findings JSON format:
    {"findings": [{"vuln_id": "V-T2-001", "evidence": "curl output...", "notes": ""}]}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Finding:
    vuln_id: str
    evidence: str = ""
    notes: str = ""


@dataclass
class CatalogEntry:
    id: str
    title: str
    service: str
    cvss: float
    tier: int
    chain: str
    status: str


@dataclass
class TriageResult:
    found: list[CatalogEntry] = field(default_factory=list)
    not_in_catalog: list[str] = field(default_factory=list)
    not_found: list[CatalogEntry] = field(default_factory=list)

    @property
    def score(self) -> float:
        return sum(e.cvss for e in self.found)

    @property
    def max_tier(self) -> int:
        return max((e.tier for e in self.found), default=0)


def _parse_catalog(catalog_path: Path) -> dict[str, CatalogEntry]:
    entries: dict[str, CatalogEntry] = {}
    tier_re = re.compile(r"## Tier (\d+)")
    row_re = re.compile(r"\|\s*(V-T\d+-\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*[^|]+\|\s*([\d.]+)\s*\|")
    current_tier = 0
    for line in catalog_path.read_text(encoding="utf-8").splitlines():
        m = tier_re.search(line)
        if m:
            current_tier = int(m.group(1))
            continue
        m = row_re.match(line)
        if m:
            vuln_id = m.group(1).strip()
            title = m.group(2).strip()
            service = m.group(3).strip()
            cvss = float(m.group(4).strip())
            entries[vuln_id] = CatalogEntry(
                id=vuln_id,
                title=title,
                service=service,
                cvss=cvss,
                tier=current_tier,
                chain="",
                status="unfound",
            )
    return entries


def _load_findings(findings_path: Path) -> list[Finding]:
    data = json.loads(findings_path.read_text(encoding="utf-8"))
    return [Finding(**f) for f in data.get("findings", [])]


def triage(
    engagement: str,
    findings_path: Path,
    catalog_path: Path,
) -> TriageResult:
    catalog = _parse_catalog(catalog_path)
    findings = _load_findings(findings_path)
    result = TriageResult()

    found_ids = {f.vuln_id for f in findings}
    for vuln_id in found_ids:
        if vuln_id in catalog:
            result.found.append(catalog[vuln_id])
        else:
            result.not_in_catalog.append(vuln_id)

    for vuln_id, entry in catalog.items():
        if vuln_id not in found_ids:
            result.not_found.append(entry)

    return result


def _write_report(result: TriageResult, engagement: str, output_path: Path) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        f"# Triage Report — {engagement}",
        f"",
        f"Generated: {now}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Findings mapped | {len(result.found)} |",
        f"| CVSS score sum | {result.score:.1f} |",
        f"| Highest tier reached | T{result.max_tier} |",
        f"| Unknown vuln IDs | {len(result.not_in_catalog)} |",
        f"| Catalog vulns unfound | {len(result.not_found)} |",
        f"",
    ]

    # Tier breakdown
    by_tier: dict[int, list[CatalogEntry]] = {}
    for e in result.found:
        by_tier.setdefault(e.tier, []).append(e)

    lines += ["## Tier scores", ""]
    for tier in sorted(by_tier):
        entries = by_tier[tier]
        tier_score = sum(e.cvss for e in entries)
        lines.append(f"### Tier {tier} — {tier_score:.1f} CVSS points")
        for e in sorted(entries, key=lambda x: x.id):
            lines.append(f"- **{e.id}**: {e.title} (CVSS {e.cvss})")
        lines.append("")

    if result.not_in_catalog:
        lines += ["## Unknown findings (not in catalog)", ""]
        for vid in result.not_in_catalog:
            lines.append(f"- {vid}")
        lines.append("")

    lines += ["## Unfound catalog vulns", ""]
    for e in sorted(result.not_found, key=lambda x: x.id):
        lines.append(f"- {e.id}: {e.title}")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Melispy triage tool")
    parser.add_argument("--engagement", required=True)
    parser.add_argument("--findings", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--score-only", action="store_true")
    args = parser.parse_args()

    if not args.findings.exists():
        print(f"ERROR: findings file not found: {args.findings}", file=sys.stderr)
        sys.exit(1)
    if not args.catalog.exists():
        print(f"ERROR: catalog not found: {args.catalog}", file=sys.stderr)
        sys.exit(1)

    result = triage(args.engagement, args.findings, args.catalog)

    if args.score_only:
        print(f"Engagement: {args.engagement}")
        print(f"Found: {len(result.found)} vulns")
        print(f"CVSS score: {result.score:.1f}")
        print(f"Highest tier: T{result.max_tier}")
        return

    output = args.output or Path(f"engagements/{args.engagement}/triage-report.md")
    _write_report(result, args.engagement, output)
    print(f"Report: {output}")
    print(f"Score: {result.score:.1f} CVSS | T{result.max_tier} reached | {len(result.found)} vulns found")


if __name__ == "__main__":
    main()
