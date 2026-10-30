#!/usr/bin/env python3
"""Antigravity & Cursor lifecycle hook enforcing the Multi-Series Definitive Tool Routing Protocol & OKF v0.2:

1. Blocks/warns on raw `vertexaisearch.cloud.google.com/grounding-api-redirect/` URLs in notes/fact-checks/cards/chapters.
2. Enforces Mandatory Bibliographic Lock: checks that any DOI (`10.xxxx/...`) or `arXiv:xxxx.xxxxx` cited in
   `research/notes/*.md`, `research/fact-checks/*.md`, `evidence-cards/*.md`, or `chapters/*.md` is locked in
   `sources.bib` / `SOURCES.md` via `academic-bib` (`crossref_lookup` / `arxiv_search` -> `add_bibtex_entry`).
3. Enforces OKF v0.2 Five-Rule Gate on `evidence-cards/*.md` edits (Rules 1, 4, 5, and required 9 sections).
4. Enforces Pre-PR Manuscript & Style Gate on `chapters/*.md`: checks `[citation needed]` markers, section-level
   metaphor collisions, forbidden phrases (`style/forbidden-phrases.md`), and inline vs. `## Notes` footnotes.
5. Enforces `structure` workflow reminder on `outline.md` / `_OUTLINE.md` edits.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

MARKER = "[citation needed]"
REDIRECT_MARKER = "vertexaisearch.cloud.google.com/grounding-api-redirect/"
STATE_FILE = Path(__file__).resolve().parent / ".pending_notice.txt"

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")
ARXIV_RE = re.compile(r"\barXiv:(\d{4}\.\d{4,5})\b", re.IGNORECASE)
INLINE_FN_RE = re.compile(r"(?<!^)\[\^([^\]]+)\](?!:)")
DEF_FN_RE = re.compile(r"^\[\^([^\]]+)\]:", re.MULTILINE)
HEADING_RE = re.compile(r"^(##+)\s+(.+)$", re.MULTILINE)
EXPOSED_SCAFFOLDING_HEADING_RE = re.compile(
    r"^(?:[IVX]+\.\s+|\d+\.\s+)?("
    r"the reader['\u2019]s contract\b|"
    r"what this chapter does not tell us\b|"
    r"what the evidence does not say\b|"
    r"what this chapter must not infer\b|"
    r"science,\s*interpretation,\s*art\b|"
    r"the puzzle\b|"
    r"competing explanations\b|"
    r"return$"
    r")",
    re.IGNORECASE,
)

METAPHOR_PATTERNS: dict[str, re.Pattern[str]] = {
    "gradient-as-debt": re.compile(r"\b(gradient as debt|accumulating debt|chain rule as debt|compounding debt)\b", re.IGNORECASE),
    "gate-as-judgment": re.compile(r"\b(gate as judgment|forget gate|selective gating|gating judgment)\b", re.IGNORECASE),
    "attention-as-valuation": re.compile(r"\b(attention as valuation|weighted valuation|value judgment made at scale)\b", re.IGNORECASE),
    "window-as-horizon": re.compile(r"\b(window as horizon|context window|finite horizon)\b", re.IGNORECASE),
    "forgetting-as-design": re.compile(r"\b(forgetting as design|selective forgetting|happy forgetting|adaptive forgetting)\b", re.IGNORECASE),
}

FORBIDDEN_PHRASES_PATTERNS: dict[str, re.Pattern[str]] = {
    "instructional-you-must": re.compile(r"\b(you should|you must)\b", re.IGNORECASE),
    "uncalibrated-science-says": re.compile(r"\b(science says|studies prove that|brain-based proof)\b", re.IGNORECASE),
    "alarmist-determinism": re.compile(r"\b(irreversibly harms|parental fate|developmental destiny)\b", re.IGNORECASE),
    "manufacturing-child": re.compile(r"\b(perfect child|ideal child)\b", re.IGNORECASE),
    "anthropomorphic-ai": re.compile(r"\b(the network thinks|the model believes|the AI wants)\b", re.IGNORECASE),
}


def _find_book_or_series_dir(path: Path) -> Path | None:
    for parent in [path] + list(path.parents):
        name = parent.name.lower()
        if (name.startswith("book-") or name == "parenthood-atlas") and parent.is_dir():
            return parent
    return None


def _is_book_chapter(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    return (
        "chapters" in parts
        and path.suffix.lower() == ".md"
        and not path.name.startswith("_")
        and path.name.lower() not in ("index.md", "readme.md")
    )


def _is_evidence_card(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    return (
        "evidence-cards" in parts
        and path.suffix.lower() == ".md"
        and path.name not in ("_TEMPLATE.md", "index.md", "README.md")
    )


def _is_research_md(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    return (
        "research" in parts
        and ("notes" in parts or "fact-checks" in parts or "extraction" in parts)
        and path.suffix.lower() == ".md"
    )


def _is_book_outline(path: Path) -> bool:
    return path.name.lower() in ("outline.md", "_outline.md")


def _is_series_manifest(path: Path) -> bool:
    return path.name.lower() == "series.yaml"


def _check_series_manifest_gates(path: Path) -> list[str]:
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        mi = data.get("marketing_intelligence") or {}
        kdp = (data.get("monetization") or {}).get("kdp") or {}
        kws = kdp.get("backend_keywords") or []
        issues: list[str] = []
        if len(mi.get("target_personas") or []) < 2:
            issues.append("fewer than 2 target_personas")
        if len(mi.get("high_intent_topic_clusters") or []) < 3:
            issues.append("fewer than 3 high_intent_topic_clusters")
        if len(mi.get("comp_title_gaps") or []) < 2:
            issues.append("fewer than 2 comp_title_gaps")
        if len(kws) != 7 or any(len(k) > 50 for k in kws):
            issues.append("kdp.backend_keywords must have exactly 7 phrases <= 50 chars each")
        if issues:
            return [f"Marketing Intelligence Gate (`{path.name}`): {'; '.join(issues)}."]
    except Exception:
        pass
    return []


def _check_bibliographic_lock(path: Path, text: str) -> list[str]:
    book_dir = _find_book_or_series_dir(path)
    if not book_dir:
        return []
    bib_candidates = [
        book_dir / "research" / "sources.bib",
        book_dir / "sources.bib",
        book_dir / "SOURCES.md",
        book_dir / "research" / "SOURCES.md",
    ]
    combined_bib = "\n".join(
        p.read_text(encoding="utf-8", errors="replace").lower()
        for p in bib_candidates
        if p.is_file()
    )

    raw_dois = {d.rstrip(".,;:)]>*") for d in DOI_RE.findall(text)}
    valid_dois = {d for d in raw_dois if "/" in d and len(d.split("/", 1)[1]) >= 3 and "xxxx" not in d.lower()}
    missing_dois = sorted(d for d in valid_dois if d.lower() not in combined_bib)

    arxiv_ids = {a for a in ARXIV_RE.findall(text)}
    missing_arxiv = sorted(a for a in arxiv_ids if a.lower() not in combined_bib)

    warnings: list[str] = []
    if missing_dois or missing_arxiv:
        items = [f"DOI:{d}" for d in missing_dois[:5]] + [f"arXiv:{a}" for a in missing_arxiv[:5]]
        warnings.append(
            f"Routing Protocol (Step 4 — Bibliographic Lock): `{path.name}` cites {', '.join(items)} "
            f"which are not yet locked in `{book_dir.name}` bibliography (`sources.bib` / `SOURCES.md`). "
            "Run `academic-bib` (`crossref_lookup` / `arxiv_search` -> `add_bibtex_entry`) and `python scripts/sync_okf_sources.py`."
        )
    return warnings


def _check_evidence_card_gates(path: Path) -> list[str]:
    try:
        from five_rule_check import check_card

        rep = check_card(path, online_retraction=False)
        issues: list[str] = []
        if not rep["rule1_urls_present"]:
            issues.append("Rule 1 fail (missing/non-http source URLs)")
        if not rep["rule4_yaml_matches_body_tokens"]:
            issues.append(f"Rule 4 fail (YAML {rep['rule4_yaml_tokens']} != body {rep['rule4_body_tokens']})")
        if not rep["rule5_wtdm_nonempty"]:
            issues.append("Rule 5 fail (`## What This Does Not Mean` missing or <= 40 chars)")
        if rep["missing_sections"]:
            issues.append(f"Missing required sections: {rep['missing_sections']}")
        if not rep.get("confounding_pass", True):
            issues.append(f"Confounding/GI attenuation fail ({rep.get('confounding_notes', 'missing or invalid classification')})")
        if not rep.get("frontmatter_pass", True):
            issues.append(f"Frontmatter schema fail (missing {rep.get('frontmatter_missing')})")
        if issues:
            return [f"OKF Five-Rule Gate (`{path.name}`): {'; '.join(issues)}."]
    except Exception:
        pass
    return []


def _check_chapter_gates(path: Path, text: str) -> list[str]:
    notices: list[str] = []
    count = text.lower().count(MARKER)
    if count:
        lines = [i + 1 for i, line in enumerate(text.splitlines()) if MARKER in line.lower()][:5]
        notices.append(
            f"Citation Gate: `{path.name}` has {count} `{MARKER}` marker(s) (first line(s): {lines}). "
            "Resolve or track in `research/fact-checks/` before merge."
        )

    defs = set(DEF_FN_RE.findall(text))
    body_before_notes = text.split("## Notes")[0] if "## Notes" in text else text
    inlines = set(INLINE_FN_RE.findall(body_before_notes))
    missing_defs = sorted(inlines - defs)
    unused_defs = sorted(defs - inlines)
    if missing_defs:
        notices.append(f"Footnote Gate: `{path.name}` has inline footnote(s) missing definitions in `## Notes`: {missing_defs}.")
    if unused_defs:
        notices.append(f"Footnote Gate: `{path.name}` has unused footnote definition(s) in `## Notes`: {unused_defs}.")

    no_bq = "\n".join(line for line in body_before_notes.splitlines() if not line.lstrip().startswith(">"))
    unquoted = re.sub(r'"[^"\n]{1,300}"|\u201c[^\u201d\n]{1,300}\u201d', '""', no_bq)
    for label, pat in FORBIDDEN_PHRASES_PATTERNS.items():
        m = pat.search(unquoted)
        if m:
            notices.append(
                f"Style Gate (`style/forbidden-phrases.md`): `{path.name}` uses forbidden phrase `{m.group(0)}` ({label})."
            )

    matches = list(HEADING_RE.finditer(body_before_notes))
    for idx, m in enumerate(matches):
        sec_title = m.group(2).strip()
        if sec_title.lower().startswith(("notes", "sources", "further reading", "linked evidence cards")):
            continue
        if EXPOSED_SCAFFOLDING_HEADING_RE.search(sec_title):
            notices.append(
                f"Organic Integration Gate (Directives I & II): `{path.name}` exposes outline scaffolding heading "
                f"`## {sec_title}` — dissolve into concentric thematic narrative prose."
            )
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body_before_notes)
        sec_body = body_before_notes[start:end]
        matched = [name for name, pat in METAPHOR_PATTERNS.items() if pat.search(sec_body)]
        if len(matched) > 1:
            notices.append(
                f"Metaphor Gate: `{path.name}` section '{sec_title}' mixes multiple controlling metaphors "
                f"({', '.join(matched)}). Series bible allows at most 1 controlling metaphor per section."
            )

    # ARC-71 / ARC-72: Anti-Leakage & Bestseller Readability Gate
    try:
        from audit_manuscript import ANTI_LEAKAGE_PATTERNS, compute_readability_metrics, load_jargon_dictionary

        for leak_label, leak_pat in ANTI_LEAKAGE_PATTERNS.items():
            m = leak_pat.search(body_before_notes)
            if m:
                notices.append(
                    f"Anti-Leakage Gate (`ARC-71`): `{path.name}` leaks `{m.group(0)}` ({leak_label}) in body prose."
                )
        lang = "es" if ("i18n" in path.parts and "es" in path.parts) else "en"
        jargon_dict = load_jargon_dictionary(ROOT, path.parent.parent)
        found_jargon = [t for t in jargon_dict if t.lower() in body_before_notes.lower()]
        if found_jargon:
            notices.append(
                f"Jargon-to-Notes Gate (`style/jargon-to-notes.yml`): `{path.name}` contains clinical terms in body prose "
                f"({', '.join(found_jargon[:5])}) — relocate to `## Notes`."
            )
        rm = compute_readability_metrics(body_before_notes, language=lang)
        if lang == "es":
            if float(rm["szigriszt"]) < 45.0:
                notices.append(
                    f"Bestseller Readability Gate (`ARC-76`): `{path.name}` Flesch-Szigriszt is {rm['szigriszt']} "
                    f"(target >= 45.0, avg sentence {rm['avg_sentence_words']}w)."
                )
        else:
            if float(rm["fk_grade"]) > 10.5:
                notices.append(
                    f"Bestseller Readability Gate (`ARC-71`): `{path.name}` Flesch-Kincaid Grade is {rm['fk_grade']} "
                    f"(target <= 10.5, avg sentence {rm['avg_sentence_words']}w)."
                )
    except Exception:
        pass

    return notices


def handle_post_tool_use(payload: dict) -> None:
    tool_call = payload.get("toolCall") or {}
    args = tool_call.get("args") or {}
    raw_path = args.get("Path") or args.get("path") or args.get("file_path") or ""
    if not raw_path:
        print("{}", flush=True)
        return

    path = Path(raw_path)
    notices: list[str] = []

    if (_is_book_chapter(path) or _is_research_md(path) or _is_evidence_card(path)) and path.is_file():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            if REDIRECT_MARKER in text.lower():
                notices.append(
                    f"Routing Protocol Violation: `{path.name}` contains raw `{REDIRECT_MARKER}` redirect URL(s). "
                    "Replace with canonical DOIs/URLs via `academic-bib` or `perplexity_search`."
                )
            notices.extend(_check_bibliographic_lock(path, text))
            if _is_book_chapter(path):
                notices.extend(_check_chapter_gates(path, text))
            if _is_evidence_card(path):
                notices.extend(_check_evidence_card_gates(path))
        except OSError:
            pass

    if _is_book_outline(path):
        notices.append(
            f"Outline Gate: `{path.as_posix()}` was edited — ensure a Linear issue with the `structure` label "
            "exists and cross-references in `chapters/` and `evidence-cards/` remain aligned."
        )

    if _is_series_manifest(path) and path.is_file():
        notices.extend(_check_series_manifest_gates(path))

    if notices:
        try:
            existing = STATE_FILE.read_text(encoding="utf-8") if STATE_FILE.is_file() else ""
            combined = (existing + "\n" + "\n".join(notices)).strip()
            STATE_FILE.write_text(combined, encoding="utf-8")
        except OSError:
            pass

    print("{}", flush=True)


def handle_post_invocation() -> None:
    if not STATE_FILE.is_file():
        print("{}", flush=True)
        return
    try:
        msg = STATE_FILE.read_text(encoding="utf-8").strip()
        STATE_FILE.unlink(missing_ok=True)
    except OSError:
        print("{}", flush=True)
        return

    if not msg:
        print("{}", flush=True)
        return

    print(
        json.dumps(
            {
                "injectSteps": [
                    {
                        "ephemeralMessage": msg,
                    }
                ]
            }
        ),
        flush=True,
    )


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "post-tool"
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    if mode == "post-invocation":
        handle_post_invocation()
    else:
        handle_post_tool_use(payload)


if __name__ == "__main__":
    main()
