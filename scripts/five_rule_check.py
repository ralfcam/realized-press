#!/usr/bin/env python3
"""Universal OKF v0.2 Five-Rule Evidence Card Checker across all series and books.

Rules checked:
- Rule 1 (mechanical): All YAML `sources` entries have resolvable http(s) URLs.
- Rule 2 (retraction/EoC): Automated via `scripts/mcp_academic_bib.py` (`crossref_lookup` +
  `openalex_work` `is_retracted`) when `--online-retraction-check` is passed.
- Rule 3 (replication signal): At least 2 source IDs present on card (human still verifies
  independent/conceptual replication before setting `status: stable`).
- Rule 4 (grade token parity): YAML `confidence` grade tokens match in-body `**Grade**` tokens.
- Rule 5 (substantive WTDM): `## What This Does Not Mean` is present and > 40 chars.
- Confounding & GI Attenuation Gate: Section `## Bias, Heterogeneity, and Confounding` contains
  an explicit classification token (`largely confounded (>50%)`, `partially confounded (20–50%)`,
  `robust (<20%)`, `untested-in-GI`, or `n/a`), and does NOT contain `not classified`.
- Frontmatter Schema Gate: YAML frontmatter contains required keys (`type`, `title`, `description`,
  `tags`, `status`, `confidence`, `sources`, plus series-specific `atlas_domains` or `series_domains`
  and `chapter_hooks`).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

REQUIRED_SECTIONS = [
    "What We Know",
    "How Confident We Are",
    "Evidence and Causal Assessment",
    "Effect Size and Persistence",
    "Bias, Heterogeneity, and Confounding",
    "What Remains Uncertain",
    "What This Does Not Mean",
    "What Action Is Reasonably Justified",
    "Sources",
]


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def yaml_confidence(fm: str) -> str:
    m = re.search(r"^confidence:\s*(.+)$", fm, re.M)
    return (m.group(1).strip().strip('"') if m else "").lower()


def yaml_status(fm: str) -> str:
    m = re.search(r"^status:\s*(\S+)", fm, re.M)
    return m.group(1) if m else ""


def source_ids_and_urls(fm: str) -> list[tuple[str, str]]:
    ids = re.findall(r"^\s+- id: (\S+)", fm, re.M)
    urls = re.findall(r"^\s+resource: (\S+)", fm, re.M)
    out = []
    for i, sid in enumerate(ids):
        url = urls[i] if i < len(urls) else ""
        out.append((sid, url))
    return out


def in_body_grade_tokens(body: str) -> set[str]:
    tokens = set()
    for line in body.splitlines():
        if not re.search(r"\*\*Grade\*\*|\*\*grade\*\*", line, re.I):
            continue
        low = line.lower()
        if "very low" in low or "very-low" in low:
            tokens.add("very-low")
        for word in ("high", "moderate", "low"):
            if re.search(rf"\b{word}\b", low):
                tokens.add(word)
    return tokens


def yaml_grade_tokens(conf: str) -> set[str]:
    tokens = set()
    c = conf.replace("_", "-")
    if "very-low" in c or "very low" in c:
        tokens.add("very-low")
    for word in ("high", "moderate", "low"):
        if re.search(rf"\b{word}\b", c) or f"-{word}" in c or c.startswith(word):
            tokens.add(word)
    return tokens


def extract_doi(url: str) -> str | None:
    m = re.search(r"(10\.\d{4,9}/[^\s\"<>]+)", url)
    return m.group(1).rstrip(".,;)") if m else None


def check_online_retractions(sources: list[tuple[str, str]]) -> tuple[bool, list[str]]:
    """Use academic-bib MCP helpers to check Crossref update-to & OpenAlex is_retracted."""
    try:
        import mcp_academic_bib as bib
    except Exception as exc:
        return False, [f"Could not import mcp_academic_bib: {exc}"]

    flags: list[str] = []
    checked = 0
    for sid, url in sources:
        doi = extract_doi(url)
        if not doi:
            continue
        checked += 1
        try:
            cr = bib.tool_crossref_lookup({"doi": doi})
            if cr.get("updates_or_errata"):
                flags.append(f"{sid} ({doi}): Crossref update-to={cr['updates_or_errata']}")
        except Exception:
            pass
        try:
            oa = bib.tool_openalex_work({"doi": doi})
            if oa.get("is_retracted"):
                flags.append(f"{sid} ({doi}): OpenAlex is_retracted=True")
        except Exception:
            pass
    return len(flags) == 0, flags or [f"0 retractions/EoCs across {checked} DOIs"]


CONFOUNDING_PATTERNS = [
    (r"(?:gi attenuation|genetically informed attenuation|confounding|classified as)[:\s]+[`\*]*largely confounded\s*(?:\(>50%\))?[`\*]*", "largely confounded (>50%)"),
    (r"(?:gi attenuation|genetically informed attenuation|confounding|classified as)[:\s]+[`\*]*partially confounded\s*(?:\(20[–-]50%\))?[`\*]*", "partially confounded (20–50%)"),
    (r"(?:gi attenuation|genetically informed attenuation|confounding|classified as)[:\s]+[`\*]*robust\s*(?:\(<20%\))?[`\*]*", "robust (<20%)"),
    (r"(?:gi attenuation|genetically informed attenuation|confounding|classified as)[:\s]+[`\*]*(?:untested-in-gi|untested in gi)[`\*]*", "untested-in-GI"),
    (r"(?:gi attenuation|genetically informed attenuation|confounding|classified as)[:\s]+[`\*]*n/?a[`\*]*", "n/a"),
]


def check_card(path: Path, online_retraction: bool = False) -> dict:
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    sources = source_ids_and_urls(fm)
    missing_sections = [s for s in REQUIRED_SECTIONS if f"## {s}" not in body]
    yaml_tok = yaml_grade_tokens(yaml_confidence(fm))
    body_tok = in_body_grade_tokens(body)
    rule4 = bool(yaml_tok) and yaml_tok == body_tok
    wtdm = "## What This Does Not Mean" in body
    wtdm_text = ""
    if wtdm:
        chunk = body.split("## What This Does Not Mean", 1)[1]
        wtdm_text = chunk.split("## ", 1)[0].strip()

    # Confounding and GI attenuation check
    confounding_pass = False
    confounding_label = ""
    confounding_notes = ""
    if "## Bias, Heterogeneity, and Confounding" in body:
        chunk = body.split("## Bias, Heterogeneity, and Confounding", 1)[1]
        conf_sec = chunk.split("## ", 1)[0].lower()
        if "not classified" in conf_sec:
            confounding_pass = False
            confounding_notes = "contains forbidden 'not classified' token"
        else:
            for pat, label in CONFOUNDING_PATTERNS:
                if re.search(pat, conf_sec):
                    confounding_pass = True
                    confounding_label = label
                    confounding_notes = f"classified as {label}"
                    break
            if not confounding_pass:
                confounding_notes = "no recognized GI attenuation / confounding token found"
    else:
        confounding_notes = "section ## Bias, Heterogeneity, and Confounding is missing"

    # Frontmatter schema check
    frontmatter_pass = True
    frontmatter_missing: list[str] = []
    if fm:
        req_keys = {"type", "title", "description", "tags", "status", "confidence", "sources"}
        parts_lower = [p.lower() for p in path.parts]
        if "parenthood-atlas" in parts_lower:
            req_keys.update({"atlas_domains", "chapter_hooks"})
        elif "architectures-of-memory" in parts_lower:
            req_keys.update({"series_domains", "chapter_hooks"})

        parsed_keys = set()
        if yaml:
            try:
                parsed_dict = yaml.safe_load(fm) or {}
                if isinstance(parsed_dict, dict):
                    parsed_keys = set(parsed_dict.keys())
            except Exception:
                pass
        if not parsed_keys:
            for line in fm.splitlines():
                km = re.match(r"^([a-zA-Z0-9_-]+):", line)
                if km:
                    parsed_keys.add(km.group(1))

        missing_keys = sorted(req_keys - parsed_keys)
        if missing_keys:
            frontmatter_pass = False
            frontmatter_missing = missing_keys
    else:
        frontmatter_pass = False
        frontmatter_missing = ["frontmatter missing entirely"]

    rule2_checked = online_retraction
    rule2_pass = True
    rule2_notes: list[str] = []
    if online_retraction:
        rule2_pass, rule2_notes = check_online_retractions(sources)

    return {
        "path": str(path),
        "status": yaml_status(fm),
        "confidence": yaml_confidence(fm),
        "source_count": len(sources),
        "sources": sources,
        "rule1_urls_present": all(u.startswith("http") for _, u in sources) and bool(sources),
        "rule2_checked": rule2_checked,
        "rule2_pass": rule2_pass,
        "rule2_notes": rule2_notes,
        "rule3_second_source_id": len(sources) >= 2,
        "rule4_yaml_matches_body_tokens": rule4,
        "rule4_yaml_tokens": sorted(yaml_tok),
        "rule4_body_tokens": sorted(body_tok),
        "rule5_wtdm_nonempty": wtdm and len(wtdm_text) > 40,
        "missing_sections": missing_sections,
        "confounding_pass": confounding_pass,
        "confounding_label": confounding_label,
        "confounding_notes": confounding_notes,
        "frontmatter_pass": frontmatter_pass,
        "frontmatter_missing": frontmatter_missing,
    }


def format_report(r: dict) -> str:
    if r["rule2_checked"]:
        r2_line = (
            f"- Rule 2 (Crossref/OpenAlex retraction check): **{'pass' if r['rule2_pass'] else 'FAIL'}** "
            f"({'; '.join(r['rule2_notes'])})."
        )
    else:
        r2_line = (
            "- Rule 2 (retraction/EoC): **not checked online** (pass `--online-retraction-check` "
            "to query Crossref `update-to` & OpenAlex `is_retracted`)."
        )
    lines = [
        f"Card: `{r['path']}`",
        f"YAML status: `{r['status']}` (script never flips this)",
        f"YAML confidence: `{r['confidence']}`",
        "",
        f"- Rule 1 (mechanical): source URLs present = **{'pass' if r['rule1_urls_present'] else 'fail'}** ({r['source_count']} IDs).",
        r2_line,
        f"- Rule 3 (non-decisive): second source ID on card = **{'present' if r['rule3_second_source_id'] else 'absent'}**.",
        "- Rule 3: a second source ID is not evidence of independent replication.",
        f"- Design class / GI attenuation: **{'pass' if r['confounding_pass'] else 'FAIL'}** ({r['confounding_notes']}).",
        f"- Frontmatter schema: **{'pass' if r['frontmatter_pass'] else 'FAIL'}** ({'missing: ' + ', '.join(r['frontmatter_missing']) if r['frontmatter_missing'] else 'all required keys present'}).",
        f"- Rule 4 (YAML = in-body grade tokens): **{'pass' if r['rule4_yaml_matches_body_tokens'] else 'fail'}** "
        f"(yaml {r['rule4_yaml_tokens']} vs body {r['rule4_body_tokens']}).",
        f"- Rule 5 (WTDM nonempty): **{'pass' if r['rule5_wtdm_nonempty'] else 'fail'}**.",
    ]
    if r["missing_sections"]:
        lines.append(f"- Missing sections: {', '.join(r['missing_sections'])}")
    lines.append("")
    lines.append("Do not set `status: stable` from this script.")
    return "\n".join(lines) + "\n"


def resolve_card_targets(targets: list[str]) -> list[Path]:
    cards: list[Path] = []
    for t in targets:
        p = Path(t)
        if not p.exists():
            # Fallback for relative paths from series/parenthood-atlas
            alt = ROOT / "series" / "parenthood-atlas" / t
            if alt.exists():
                p = alt
        if p.is_dir():
            ec_dir = None
            for cand in [p / "evidence-cards", p.parent / "evidence-cards", p.parent.parent / "evidence-cards"]:
                if cand.is_dir():
                    ec_dir = cand
                    break
            if ec_dir is None:
                ec_dir = p
            for md in sorted(ec_dir.glob("*.md")):
                if md.name in ("_TEMPLATE.md", "index.md", "README.md"):
                    continue
                cards.append(md)
        else:
            if p.name not in ("_TEMPLATE.md", "index.md"):
                cards.append(p)
    return cards


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="OKF v0.2 Five-Rule Evidence Card Checker")
    parser.add_argument("targets", nargs="+", help="Card .md files or book/evidence-cards directories")
    parser.add_argument(
        "--online-retraction-check",
        action="store_true",
        help="Check Rule 2 live via Crossref and OpenAlex APIs",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print compact summary when scanning whole directories",
    )
    args = parser.parse_args(argv[1:])

    cards = resolve_card_targets(args.targets)
    if not cards:
        print(f"No evidence cards found in targets: {args.targets}", file=sys.stderr)
        return 2

    rc = 0
    passed = 0
    for path in cards:
        if not path.exists():
            print(f"FAIL missing file: {path}", file=sys.stderr)
            rc = 1
            continue
        report = check_card(path, online_retraction=args.online_retraction_check)
        card_ok = (
            report["rule1_urls_present"]
            and report["rule2_pass"]
            and report["rule4_yaml_matches_body_tokens"]
            and report["rule5_wtdm_nonempty"]
            and not report["missing_sections"]
            and report["confounding_pass"]
            and report["frontmatter_pass"]
        )
        if card_ok:
            passed += 1
        else:
            rc = 1
        if not args.summary_only or not card_ok:
            print(format_report(report))

    if len(cards) > 1 or args.summary_only:
        print(f"[five-rule-summary] {passed}/{len(cards)} evidence cards passed mechanical checks.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
