#!/usr/bin/env python3
"""Manuscript, Continuity & OKF Hygiene Auditor for Multi-Series Monorepo.

Performs:
1. Metaphor collision analysis per chapter section (max 1 controlling metaphor/section)
2. Footnote integrity & cross-chapter label collision detection
3. Character continuity & first-mention tracking (against characters.md)
4. Forbidden-phrase & redirect-URL epistemic hygiene check (against style/forbidden-phrases.md)
5. OKF v0.2 Evidence Cards summary (via scripts/five_rule_check.py)
6. Residual fact-check & [citation needed] debt summary
7. Optional long-context Gemini holistic review (--gemini, requires GEMINI_API_KEY)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

from five_rule_check import check_card, resolve_card_targets
from merge_book_chapters import iter_chapter_files, repo_root, resolve_book_path

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
    "raw-grounding-redirect": re.compile(r"vertexaisearch\.cloud\.google\.com/grounding-api-redirect/", re.IGNORECASE),
}

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


def find_series_file(root: Path, book_path: Path, filename: str) -> Path | None:
    for candidate in (
        book_path / filename,
        book_path.parent / filename,
        root / "series" / "architectures-of-memory" / filename,
        root / filename,
    ):
        if candidate.is_file():
            return candidate
    return None


def load_characters(root: Path, book_path: Path) -> list[tuple[str, str]]:
    """Return list of (full_heading, surname_key) from characters.md."""
    char_file = find_series_file(root, book_path, "characters.md")
    if not char_file:
        return []
    out: list[tuple[str, str]] = []
    for line in char_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            raw = line.removeprefix("### ").strip()
            clean = re.sub(r"\s*\([^)]*\)", "", raw).strip()
            parts = [p.strip() for p in re.split(r"&|,", clean) if p.strip()]
            for p in parts:
                surname = p.split()[-1]
                out.append((p, surname))
    return out


def split_sections(md_text: str) -> list[tuple[str, str]]:
    """Return list of (section_title, section_body) for a chapter."""
    matches = list(HEADING_RE.finditer(md_text))
    if not matches:
        return [("Body", md_text)]
    sections: list[tuple[str, str]] = []
    for idx, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md_text)
        sections.append((title, md_text[start:end]))
    return sections


def strip_quoted_spans(text: str) -> str:
    """Remove blockquotes and double-quoted dialogue before checking instructional phrases."""
    no_bq = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))
    return re.sub(r'"[^"\n]{1,300}"|\u201c[^\u201d\n]{1,300}\u201d', '""', no_bq)


def run_gemini_review(root: Path, book_path: Path, chapters: list[Path]) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "_Skipped (`GEMINI_API_KEY` not set in environment)._"

    bible_file = find_series_file(root, book_path, "series-bible.md") or find_series_file(root, book_path, "COMPOSITION.md")
    chars_file = find_series_file(root, book_path, "characters.md")
    outline_file = (
        book_path / "outline.md"
        if (book_path / "outline.md").is_file()
        else (book_path / "chapters" / "_OUTLINE.md" if (book_path / "chapters" / "_OUTLINE.md").is_file() else None)
    )
    bible = bible_file.read_text(encoding="utf-8") if bible_file else ""
    chars = chars_file.read_text(encoding="utf-8") if chars_file else ""
    outline = outline_file.read_text(encoding="utf-8") if outline_file else ""
    manuscript = "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in chapters)

    prompt = (
        f"You are the Series Editor auditing '{book_path.name}'.\n"
        "Evaluate the complete manuscript below against the Compositional/Series Bible, Characters guide, and Outline.\n"
        "Provide a concise, high-signal markdown audit covering:\n"
        "1. Voice & Tone Consistency (analytic, calm, concrete scenes/anomalies, non-deterministic)\n"
        "2. Three-Lens Balance (Technical/Science -> Organizational/Interpretation -> Philosophical/Art)\n"
        "3. Cross-Chapter Argument Progression & Redundancies\n"
        "4. Top 5 Specific Line/Section Edit Recommendations\n\n"
        f"## SERIES BIBLE / COMPOSITION\n{bible}\n\n## CHARACTERS\n{chars}\n\n## BOOK OUTLINE\n{outline}\n\n## MANUSCRIPT\n{manuscript}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates") or []
            if candidates:
                parts = (candidates[0].get("content") or {}).get("parts") or []
                return "".join(p.get("text", "") for p in parts).strip()
            return "_Gemini returned no candidates._"
    except Exception as exc:
        return f"_Gemini API call failed: {exc}_"


def audit_book(book_path: Path, use_gemini: bool = False) -> tuple[str, bool]:
    root = repo_root()
    chapters_dir = book_path / "chapters"
    chapters = iter_chapter_files(chapters_dir)
    if not chapters:
        return f"# Audit Report: `{book_path.name}`\n\nNo chapters found in `{chapters_dir}`.\n", True

    characters = load_characters(root, book_path)
    char_mentions: dict[str, list[str]] = defaultdict(list)
    fn_defs_across_book: dict[str, list[str]] = defaultdict(list)

    chapter_rows: list[str] = []
    metaphor_collisions: list[str] = []
    fn_issues: list[str] = []
    forbidden_hits: list[str] = []
    scaffolding_hits: list[str] = []
    citation_needed_total = 0

    for ch in chapters:
        text = ch.read_text(encoding="utf-8")
        words = len(text.split())
        cn_count = text.lower().count("[citation needed]")
        citation_needed_total += cn_count

        defs = set(DEF_FN_RE.findall(text))
        body_before_notes = text.split("## Notes")[0] if "## Notes" in text else text
        inlines = set(INLINE_FN_RE.findall(body_before_notes))

        for d in defs:
            fn_defs_across_book[d].append(ch.name)

        missing_defs = sorted(inlines - defs)
        unused_defs = sorted(defs - inlines)
        if missing_defs:
            fn_issues.append(f"- `{ch.name}`: inline footnote(s) missing definition: `{missing_defs}`")
        if unused_defs:
            fn_issues.append(f"- `{ch.name}`: defined footnote(s) never cited inline: `{unused_defs}`")

        sections = split_sections(body_before_notes)
        for sec_title, sec_body in sections:
            if sec_title.lower().startswith(("notes", "sources", "further reading", "linked evidence cards")):
                continue
            if EXPOSED_SCAFFOLDING_HEADING_RE.search(sec_title):
                scaffolding_hits.append(
                    f"- `{ch.name}`: exposed scaffolding heading `## {sec_title}` (must be dissolved into organic narrative movements)"
                )
            matched = [name for name, pat in METAPHOR_PATTERNS.items() if pat.search(sec_body)]
            if len(matched) > 1:
                metaphor_collisions.append(
                    f"- `{ch.name}` → **{sec_title}**: multiple controlling metaphors (`{', '.join(matched)}`)"
                )

        unquoted_body = strip_quoted_spans(body_before_notes)
        for label, pat in FORBIDDEN_PHRASES_PATTERNS.items():
            m = pat.search(unquoted_body)
            if m:
                forbidden_hits.append(f"- `{ch.name}`: forbidden pattern `{label}` (`{m.group(0)}`)")

        for full_name, surname in characters:
            if re.search(rf"\b{re.escape(surname)}\b", body_before_notes):
                char_mentions[full_name].append(ch.stem[:2])

        chapter_rows.append(f"| `{ch.name}` | {words:,} | {len(defs)} | {cn_count} |")

    duplicate_fns = {k: v for k, v in fn_defs_across_book.items() if len(v) > 1}

    fc_dir = book_path / "research" / "fact-checks"
    open_fc_items: list[str] = []
    if fc_dir.is_dir():
        for fc in sorted(fc_dir.glob("*.md")):
            for i, line in enumerate(fc.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"^\s*-\s*\[ \]", line):
                    open_fc_items.append(f"- `{fc.name}:{i}`: {line.strip()}")

    bib_path = (
        book_path / "research" / "sources.bib"
        if (book_path / "research" / "sources.bib").is_file()
        else book_path / "sources.bib"
    )
    bib_entries = 0
    if bib_path.is_file():
        bib_entries = len(re.findall(r"^@\w+\s*\{", bib_path.read_text(encoding="utf-8"), re.MULTILINE))

    ec_cards = resolve_card_targets([str(book_path)])
    ec_passed = 0
    ec_failures: list[str] = []
    for cpath in ec_cards:
        rep = check_card(cpath, online_retraction=False)
        ok = (
            rep["rule1_urls_present"]
            and rep["rule4_yaml_matches_body_tokens"]
            and rep["rule5_wtdm_nonempty"]
            and not rep["missing_sections"]
        )
        if ok:
            ec_passed += 1
        else:
            ec_failures.append(f"- `{cpath.name}`: failed mechanical 5-rule check")

    lines = [
        f"# Manuscript, Continuity & OKF Audit — `{book_path.name}`",
        "",
        "## 1. Overview Metrics",
        f"- **Chapters audited:** {len(chapters)}",
        f"- **Total words:** {sum(len(c.read_text(encoding='utf-8').split()) for c in chapters):,}",
        f"- **Unresolved `[citation needed]` markers in prose:** {citation_needed_total}",
        f"- **BibTeX entries in `sources.bib`:** {bib_entries}",
        f"- **OKF v0.2 Evidence Cards (`evidence-cards/`):** {ec_passed}/{len(ec_cards)} passing mechanical 5-rule gate",
        "",
        "| Chapter | Words | Footnotes | `[citation needed]` |",
        "| :--- | ---: | ---: | ---: |",
        *chapter_rows,
        "",
        "## 2. Metaphor Collision Check (Rule: Max 1 Controlling Metaphor / Section)",
    ]
    if metaphor_collisions:
        lines.extend(metaphor_collisions)
    else:
        lines.append("- **Pass:** No multi-metaphor collisions detected within any single chapter section.")

    lines.extend(["", "## 3. Footnote Integrity & Cross-Chapter Collisions"])
    if fn_issues:
        lines.extend(fn_issues)
    else:
        lines.append("- **Pass:** Every chapter's inline `[^key]` matches its local `## Notes` definitions.")

    if duplicate_fns:
        lines.append(
            f"- **Notice ({len(duplicate_fns)} shared footnote keys across chapters):** "
            + ", ".join(f"`[^{k}]` ({', '.join(v)})" for k, v in sorted(duplicate_fns.items()))
        )

    lines.extend(["", "## 4. Forbidden-Phrase & Epistemic Hygiene Check (`style/forbidden-phrases.md`)"])
    if forbidden_hits:
        lines.extend(forbidden_hits)
    else:
        lines.append("- **Pass:** Zero forbidden phrases or raw redirect URLs detected in unquoted chapter prose.")

    lines.extend(["", "## 4b. Organic Narrative Integration Check (Directives I & II — No Exposed Scaffolding Headings)"])
    if scaffolding_hits:
        lines.extend(scaffolding_hits)
    else:
        lines.append("- **Pass:** Zero exposed scaffolding or standalone epistemic segments detected across chapters.")

    lines.extend(["", "## 5. OKF v0.2 Five-Rule Evidence Card Gate (`evidence-cards/`)"])
    if ec_failures:
        lines.extend(ec_failures)
    else:
        lines.append(f"- **Pass:** All {len(ec_cards)} OKF v0.2 evidence card(s) pass mechanical Rules 1, 4, and 5.")

    if char_mentions:
        lines.extend(
            [
                "",
                "## 6. Character Continuity Map (`characters.md`)",
                "| Character | First Mention | Chapters Appearing |",
                "| :--- | :--- | :--- |",
            ]
        )
        for full_name, _ in characters:
            chs = char_mentions.get(full_name, [])
            if chs:
                lines.append(f"| {full_name} | Ch.{chs[0]} | {', '.join(f'Ch.{c}' for c in chs)} |")

    lines.extend(["", "## 7. Residual Fact-Check Action Items (`research/fact-checks/*.md`)"])
    if open_fc_items:
        lines.extend(open_fc_items)
    else:
        lines.append("- **Pass:** No unchecked items in `research/fact-checks/`.")

    if use_gemini:
        lines.extend(["", "## 8. Long-Context Gemini 2.5 Pro Editorial Review", ""])
        lines.append(run_gemini_review(root, book_path, chapters))

    strict_ok = (
        not metaphor_collisions
        and not fn_issues
        and not forbidden_hits
        and not ec_failures
        and citation_needed_total == 0
    )
    return "\n".join(lines) + "\n", strict_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a book manuscript for continuity, metaphors, OKF cards, and citations.")
    parser.add_argument("book", type=Path, help="Book or series directory (e.g. series/architectures-of-memory/book-01-vanishing-signal or series/parenthood-atlas)")
    parser.add_argument("--output", type=Path, default=None, help="Optional file path to write markdown report")
    parser.add_argument("--gemini", action="store_true", help="Run long-context Gemini 2.5 Pro holistic review")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any audit gate fails")
    args = parser.parse_args()

    root = repo_root()
    book_path = resolve_book_path(root, args.book)
    if not book_path.is_dir():
        print(f"error: directory not found: {book_path}", file=sys.stderr)
        sys.exit(1)

    report, strict_ok = audit_book(book_path, use_gemini=args.gemini)
    if args.output:
        out_path = args.output.resolve() if args.output.is_absolute() else (root / args.output).resolve()
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote audit report to {out_path}")
    else:
        sys.stdout.buffer.write(report.encode("utf-8"))

    if args.strict and not strict_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
