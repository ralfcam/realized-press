#!/usr/bin/env python3
"""Realized Press BWE — Marketing Intelligence & Data-Driven Topic Selection Engine.

Analyzes series manifests (`series.yaml`), bibliographic velocity (`sources.bib`),
and OKF v0.2 Evidence Cards (`evidence-cards/*.md`) to:
1. Validate Amazon KDP & retail metadata readiness (BISAC codes, 7 KDP backend keyword slots,
   comp-title gap thesis, target personas, search-intent topic clusters).
2. Measure Bibliographic Recency & Frontier Signal from `sources.bib`.
3. Rank top-of-funnel Lead-Magnet / Public Evidence Brief candidates from `evidence-cards/*.md`
   based on certainty grade, stability, and `## What This Does Not Mean` myth-busting hooks
   for the internally developed marketing & serial-membership site.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def extract_bib_years(series_dir: Path) -> list[int]:
    years: list[int] = []
    for bib in sorted(series_dir.rglob("sources.bib")):
        if "preliminary" in bib.parts:
            continue
        text = bib.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\byear\s*=\s*[\"{]?(\d{4})[\"}]?", text, re.IGNORECASE):
            years.append(int(m.group(1)))
    return years


def extract_lead_magnet_cards(series_dir: Path, limit: int = 5) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for card_path in sorted(series_dir.rglob("evidence-cards/*.md")):
        if card_path.name.startswith("_") or card_path.name.lower() in {"index.md", "readme.md"}:
            continue
        if "preliminary" in card_path.parts:
            continue
        text = card_path.read_text(encoding="utf-8", errors="replace")
        title_m = re.search(r'^title:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        status_m = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
        conf_m = re.search(r"^confidence:\s*(\S+)", text, re.MULTILINE)
        not_mean_m = re.search(
            r"^##\s+What This Does Not Mean\s*\n+(.+?)(?=\n##\s+|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        hook = ""
        if not_mean_m:
            first_line = not_mean_m.group(1).strip().splitlines()[0].strip()
            hook = re.sub(r"^[-*]\s+", "", first_line)
            if len(hook) > 140:
                hook = hook[:137] + "..."
        status = status_m.group(1) if status_m else "draft"
        conf = conf_m.group(1) if conf_m else "unknown"
        score = (2 if status == "stable" else 1) + (2 if "high" in conf else 1)
        candidates.append(
            {
                "id": card_path.stem,
                "title": title_m.group(1) if title_m else card_path.stem,
                "status": status,
                "confidence": conf,
                "hook": hook,
                "score": str(score),
            }
        )
    candidates.sort(key=lambda c: (-int(c["score"]), c["id"]))
    return candidates[:limit]


def analyze_series(series_dir: Path) -> str:
    manifest_path = series_dir / "series.yaml"
    if not manifest_path.is_file():
        return f"## `{series_dir.name}` — Missing `series.yaml`\n"

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    title = data.get("title", series_dir.name)
    subtitle = data.get("subtitle", "")
    mi = data.get("marketing_intelligence", {})
    mon = data.get("monetization", {})
    kdp = mon.get("kdp", {})
    site = mon.get("owned_marketing_site", {})

    personas = mi.get("target_personas", [])
    clusters = mi.get("high_intent_topic_clusters", [])
    comps = mi.get("comp_title_gaps", [])
    kdp_keywords = kdp.get("backend_keywords", [])
    bisac = kdp.get("bisac_categories", [])

    years = extract_bib_years(series_dir)
    recent_2015_plus = sum(1 for y in years if y >= 2015)
    recent_2020_plus = sum(1 for y in years if y >= 2020)
    decade_counts = Counter((y // 10) * 10 for y in years)

    lead_cards = extract_lead_magnet_cards(series_dir, limit=5)

    # Readiness checks
    checks = [
        ("Target personas defined (>=2)", len(personas) >= 2),
        ("High-intent search/topic clusters defined (>=3)", len(clusters) >= 3),
        ("Competitive review-gap thesis defined (>=2 comps)", len(comps) >= 2),
        ("Amazon KDP 7 backend keyword phrases populated (<=50 chars each)", len(kdp_keywords) == 7 and all(len(k) <= 50 for k in kdp_keywords)),
        ("BISAC category codes assigned (>=2)", len(bisac) >= 2),
        ("Owned marketing site tiers configured", len(site.get("tiers", [])) >= 2),
    ]
    passed = sum(1 for _, ok in checks if ok)

    lines = [
        f"# Marketing Intelligence & Topic Scorecard — *{title}*",
        f"- **Manifest:** `{manifest_path.relative_to(repo_root()).as_posix()}`",
        f"- **Subtitle / Positioning Hook:** *{subtitle}*",
        f"- **Market Readiness Score:** **{passed}/{len(checks)} checks passed**",
        "",
        "## 1. Demand Signals, Personas & Competitive Gap Thesis",
        "### Target Personas",
    ]
    for p in personas:
        lines.append(f"- {p}")
    lines.append("\n### High-Intent Topic & Search Clusters (Driving Chapter/Book Selection)")
    for c in clusters:
        lines.append(f"- {c}")
    lines.append("\n### Competitive Market & Review-Gap Analysis")
    for comp in comps:
        lines.append(f"- {comp}")

    lines.extend(
        [
            "",
            "## 2. Amazon KDP & Multi-Retailer Metadata Audit",
            f"- **BISAC Categories ({len(bisac)}):** {', '.join(f'`{b}`' for b in bisac)}",
            f"- **KDP Backend Keywords ({len(kdp_keywords)}/7 slots):**",
        ]
    )
    for idx, kw in enumerate(kdp_keywords, 1):
        lines.append(f"  {idx}. `{kw}` ({len(kw)}/50 chars)")

    lines.extend(
        [
            "",
            "## 3. Bibliographic Recency & Citation Velocity (`sources.bib`)",
            f"- **Total verified citations:** {len(years)}",
            f"- **Post-2015 literature:** {recent_2015_plus} ({(recent_2015_plus / len(years) * 100) if years else 0:.1f}%)",
            f"- **Post-2020 frontier literature:** {recent_2020_plus} ({(recent_2020_plus / len(years) * 100) if years else 0:.1f}%)",
            f"- **Decade distribution:** " + ", ".join(f"{d}s: {cnt}" for d, cnt in sorted(decade_counts.items())),
            "",
            "## 4. Top Owned-Marketing-Site Lead Magnets (OKF v0.2 Evidence Cards)",
            "| Card ID | Status | Grade | Counter-Intuitive / Myth-Busting Hook (`What This Does Not Mean`) |",
            "| :--- | :--- | :--- | :--- |",
        ]
    )
    for c in lead_cards:
        lines.append(f"| `{c['id']}` | `{c['status']}` | `{c['confidence']}` | {c['hook']} |")

    lines.append("\n## 5. Readiness Gate Checklist")
    for label, ok in checks:
        mark = "PASS" if ok else "FAIL"
        lines.append(f"- [{mark}] {label}")
    lines.append("")
    return "\n".join(lines)


def discover_frontier_topics(query: str, limit: int = 5, min_year: int = 2022) -> str:
    current_year = 2026
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://api.openalex.org/works?search={encoded_q}&filter=publication_year:{min_year}-{current_year},is_retracted:false&sort=cited_by_count:desc&per-page=25"
    headers = {"User-Agent": "RealizedPressBWE/1.0 (mailto:admin@realizedpress.com)"}

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return f"# Upstream Frontier Topic Radar — Error querying OpenAlex: {e}\n"

    results = data.get("results") or []
    total_found = data.get("meta", {}).get("count", 0)

    candidates = []
    topic_counter = Counter()
    keyword_counter = Counter()

    for w in results:
        title = w.get("title") or "Untitled"
        year = w.get("publication_year") or current_year
        citations = w.get("cited_by_count") or 0
        doi = w.get("doi") or ""
        age = max(1, current_year - year)
        velocity = citations / age

        pt = w.get("primary_topic") or {}
        if pt.get("display_name"):
            topic_counter[pt["display_name"]] += 1

        for kw in w.get("keywords") or []:
            if kw.get("display_name"):
                keyword_counter[kw["display_name"].lower()] += 1

        candidates.append(
            {
                "title": title,
                "year": year,
                "citations": citations,
                "velocity": velocity,
                "doi": doi,
                "topic": pt.get("display_name", "General"),
                "field": (pt.get("field") or {}).get("display_name", "Interdisciplinary"),
            }
        )

    candidates.sort(key=lambda x: -x["velocity"])
    top_candidates = candidates[:limit]

    lines = [
        f"# Upstream Frontier Topic Radar — Query: *\"{query}\"*",
        f"- **Literature Scope:** OpenAlex indexed works ({min_year}–{current_year})",
        f"- **Total Relevant Works Identified:** {total_found:,}",
        "",
        "## 1. High-Velocity Frontier Citation Clusters (Candidate Topics)",
    ]
    for topic, count in topic_counter.most_common(5):
        lines.append(f"- **{topic}** ({count} flagship high-velocity papers)")

    lines.extend(
        [
            "",
            "## 2. Emerging Keyword Signals",
            "- " + ", ".join(f"`{k}` ({cnt})" for k, cnt in keyword_counter.most_common(8)),
            "",
            "## 3. Top Candidate Seed Works for OKF v0.2 Evidence Cards",
            "| Title | Year | Citations | Velocity (cites/yr) | Primary Topic / Field | DOI |",
            "| :--- | :---: | :---: | :---: | :--- | :--- |",
        ]
    )
    for c in top_candidates:
        doi_link = f"[{c['doi'].replace('https://doi.org/', '')}]({c['doi']})" if c['doi'] else "N/A"
        lines.append(f"| {c['title']} | {c['year']} | {c['citations']} | {c['velocity']:.1f}/yr | {c['topic']} ({c['field']}) | {doi_link} |")

    lines.extend(
        [
            "",
            "## 4. Next Actions for Series / Book Scaffolding",
            f"- Initialize new series manifest: `python scripts/init_series.py --series <slug> --title \"<Title>\"`",
            "- Author seed OKF v0.2 evidence cards using the verified DOIs above.",
            "- Verify with `python scripts/five_rule_check.py series/<slug>/book-01-<book-slug> --online-retraction-check`.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BWE Marketing Intelligence & Topic Scorecard.")
    parser.add_argument("--series", default=None, help="Series directory or slug (omit to audit all series)")
    parser.add_argument("--discover", default=None, help="Upstream search query to discover frontier citation-velocity topics via OpenAlex")
    parser.add_argument("--limit", type=int, default=5, help="Max candidate seed cards to return for topic discovery")
    args = parser.parse_args()

    if args.discover:
        print(discover_frontier_topics(args.discover, limit=args.limit))
        return 0

    root = repo_root()
    if args.series:
        target = Path(args.series)
        if not target.is_dir():
            target = root / "series" / args.series
        series_dirs = [target.resolve()]
    else:
        series_dirs = sorted(p.parent for p in (root / "series").glob("*/series.yaml"))

    reports = [analyze_series(d) for d in series_dirs]
    print("\n---\n\n".join(reports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
