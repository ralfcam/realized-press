#!/usr/bin/env python3
"""Manuscript, Continuity, OKF Hygiene & Bestseller Readability Auditor for Multi-Series Monorepo.

Performs:
1. Metaphor collision analysis per chapter section (max 1 controlling metaphor/section)
2. Footnote integrity & cross-chapter label collision detection
3. Character continuity & first-mention tracking (against characters.md)
4. Forbidden-phrase & redirect-URL epistemic hygiene check (against style/forbidden-phrases.md)
4b. Organic Narrative Integration check (no exposed scaffolding headings)
5. OKF v0.2 Evidence Cards summary (via scripts/five_rule_check.py)
6. Bestseller Readability, Jargon-to-Notes & Anti-Leakage Audit (ARC-71 / ARC-72, style/jargon-to-notes.yml)
7. Character continuity map & Residual fact-check / [citation needed] debt summary
8. Optional long-context Gemini holistic review (--gemini, requires GEMINI_API_KEY)
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

import yaml

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

SPANISH_FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "instructional-debes": re.compile(r"\b(debes|tienes que|hay que)\b", re.IGNORECASE),
    "uncalibrated-ciencia-dice": re.compile(r"\b(la ciencia dice|los estudios demuestran que|está científicamente probado)\b", re.IGNORECASE),
    "alarmist-determinismo": re.compile(r"\b(daña de forma irreversible|arruina|destruye|destino del desarrollo|destino parental)\b", re.IGNORECASE),
    "manufacturing-nino-perfecto": re.compile(r"\b(niño perfecto|hijo perfecto|niño ideal|crianza óptima|optimizar el desarrollo|optimizar a tu hijo)\b", re.IGNORECASE),
    "neuro-sensationalism": re.compile(r"\b(prueba cerebral de que|pruebas basadas en el cerebro|diseñado evolutivamente para)\b", re.IGNORECASE),
    "cliche-transicion": re.compile(r"\b(profundizar en|adentrarnos en|sumergirnos en|tapiz|cambia las reglas del juego|cambio de juego|papel crucial|papel clave|testimonio de)\b", re.IGNORECASE),
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

ANTI_LEAKAGE_PATTERNS: dict[str, re.Pattern[str]] = {
    "inline-md-filename": re.compile(r"\b[a-z0-9-]+\.md\b", re.IGNORECASE),
    "backticked-footnote": re.compile(r"`\[\^[^\]]+\]`"),
    "harness-meta-escalation": re.compile(r"\bProgressive Lens Escalation\b", re.IGNORECASE),
    "harness-meta-three-tier": re.compile(
        r"\b(three-tier causal resolution|At the \*\*(?:first|second|third) tier)\b", re.IGNORECASE
    ),
}

ABBREV_RE = re.compile(r"\b(vs|et al|e\.g|i\.e|Dr|Mr|Mrs|Ms|St|U\.S|U\.K|No|Fig|Ch)\.", re.IGNORECASE)


def count_syllables(word: str) -> int:
    """Estimate English syllables for Flesch-Kincaid Grade Level calculation."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    vowels = re.findall(r"[aeiouy]{1,2}", w)
    return max(1, len(vowels))


def count_syllables_es(word: str) -> int:
    """Count syllables in Spanish according to phonotactic rules (diphthongs, triphthongs, hiatus)."""
    w = word.lower().strip()
    w = re.sub(r"[^a-záéíóúüñ]", "", w)
    if not w:
        return 0
    if w.endswith("y"):
        w = w[:-1] + "i"
    # Replace triphthongs with single vowel placeholder (weak + strong + weak)
    w = re.sub(r"[iuü][aeoáéó][iuü]", "V", w, flags=re.I)
    # Replace diphthongs with single vowel placeholder (tonic weak í/ú do NOT form diphthongs)
    w = re.sub(r"[iuü][aeoáéó]", "V", w, flags=re.I)
    w = re.sub(r"[aeoáéó][iuü]", "V", w, flags=re.I)
    w = re.sub(r"[iuü][iuü]", "V", w, flags=re.I)  # iu, ui
    vowels = re.findall(r"[aeiouáéíóúüV]", w, flags=re.I)
    return max(1, len(vowels))


def compute_readability_metrics(body_before_notes: str, language: str = "en") -> dict[str, float | int]:
    """Compute Flesch-Kincaid / Flesch-Szigriszt, avg sentence length, and long-sentence count on body prose."""
    # Remove headings, inline footnotes, markdown emphasis, and math tokens
    lines = [
        line.strip()
        for line in body_before_notes.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    clean = " ".join(lines)
    clean = INLINE_FN_RE.sub("", clean)
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = re.sub(r"\$[^$]+\$", " formula ", clean)
    clean = re.sub(r"[*_`~]", "", clean)
    clean_no_abbrev = ABBREV_RE.sub(r"\1", clean)

    raw_sentences = [s.strip() for s in re.split(r"[.!?]+(?:\s+|$)", clean_no_abbrev) if s.strip()]
    sentence_word_counts: list[int] = []
    all_words: list[str] = []

    word_regex = r"[A-Za-z0-9áéíóúüñÁÉÍÓÚÜÑ']+" if language == "es" else r"[A-Za-z0-9']+"
    for sent in raw_sentences:
        w_list = re.findall(word_regex, sent)
        if w_list:
            sentence_word_counts.append(len(w_list))
            all_words.extend(w_list)

    total_words = len(all_words)
    total_sentences = max(1, len(sentence_word_counts))
    total_syllables = sum(
        count_syllables_es(w) if language == "es" else count_syllables(w)
        for w in all_words
    )

    if total_words == 0:
        return {
            "fk_grade": 0.0,
            "szigriszt": 0.0,
            "avg_sentence_words": 0.0,
            "max_sentence_words": 0,
            "long_sentences_over_35": 0,
        }

    avg_sent = total_words / total_sentences

    if language == "es":
        # Flesch-Szigriszt (INFLESZ scale): 206.835 - 62.3 * (syllables / words) - (words / sentences)
        szigriszt = 206.835 - (62.3 * (total_syllables / total_words)) - avg_sent
        long_over = sum(1 for c in sentence_word_counts if c > 40)
        max_sent = max(sentence_word_counts) if sentence_word_counts else 0
        return {
            "fk_grade": 0.0,
            "szigriszt": round(szigriszt, 1),
            "avg_sentence_words": round(avg_sent, 1),
            "max_sentence_words": max_sent,
            "long_sentences_over_35": long_over,
        }
    else:
        avg_syl = total_syllables / total_words
        fk_grade = 0.39 * avg_sent + 11.8 * avg_syl - 15.59
        long_over_35 = sum(1 for c in sentence_word_counts if c > 35)
        max_sent = max(sentence_word_counts) if sentence_word_counts else 0
        return {
            "fk_grade": round(fk_grade, 1),
            "szigriszt": 0.0,
            "avg_sentence_words": round(avg_sent, 1),
            "max_sentence_words": max_sent,
            "long_sentences_over_35": long_over_35,
        }


def load_jargon_dictionary(root: Path, book_path: Path | None = None) -> dict[str, str]:
    candidates = []
    if book_path:
        candidates.extend([
            book_path / "style" / "jargon-to-notes.yml",
            book_path.parent / "style" / "jargon-to-notes.yml",
            book_path.parent.parent / "style" / "jargon-to-notes.yml",
        ])
    candidates.append(root / "style" / "jargon-to-notes.yml")
    for jf in candidates:
        if jf.is_file():
            try:
                data = yaml.safe_load(jf.read_text(encoding="utf-8")) or {}
                return {str(k): str(v) for k, v in (data.get("relocate_to_notes") or {}).items()}
            except Exception:
                continue
    return {}


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


def audit_book(book_path: Path, use_gemini: bool = False, bestseller_strict: bool = False) -> tuple[str, bool]:
    root = repo_root()
    chapters_dir = book_path / "chapters"
    chapters = iter_chapter_files(chapters_dir)
    if not chapters:
        return f"# Audit Report: `{book_path.name}`\n\nNo chapters found in `{chapters_dir}`.\n", True

    manifest_file = (
        book_path / "series.yaml"
        if (book_path / "series.yaml").is_file()
        else (
            book_path.parent / "series.yaml"
            if (book_path.parent / "series.yaml").is_file()
            else (book_path.parent.parent / "series.yaml")
        )
    )
    language = "en"
    szigriszt_min = 45.0
    max_avg_sentence_words = 19.0
    max_fk_grade = 10.5
    if manifest_file.is_file():
        try:
            manifest_data = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
            rt = manifest_data.get("readability_targets") or {}
            language = rt.get("language") or manifest_data.get("locale") or ("es" if "es" in book_path.parts else "en")
            szigriszt_min = float(rt.get("szigriszt_min", 65.0))
            max_avg_sentence_words = float(rt.get("max_avg_sentence_words", 22.0 if language == "es" else 19.0))
            max_fk_grade = float(rt.get("max_flesch_kincaid_grade", 10.5))
        except Exception:
            pass
    elif "es" in book_path.parts:
        language = "es"
        max_avg_sentence_words = 22.0

    forbidden_patterns = SPANISH_FORBIDDEN_PATTERNS if language == "es" else FORBIDDEN_PHRASES_PATTERNS
    anti_leakage_patterns = dict(ANTI_LEAKAGE_PATTERNS)
    if language == "es":
        anti_leakage_patterns["harness-meta-tres-niveles"] = re.compile(
            r"\b(resolución causal en tres niveles|en el \*\*(?:primer|segundo|tercer) nivel)\b",
            re.IGNORECASE,
        )

    characters = load_characters(root, book_path)
    jargon_dict = load_jargon_dictionary(root, book_path)
    char_mentions: dict[str, list[str]] = defaultdict(list)
    fn_defs_across_book: dict[str, list[str]] = defaultdict(list)

    chapter_rows: list[str] = []
    readability_rows: list[str] = []
    metaphor_collisions: list[str] = []
    fn_issues: list[str] = []
    forbidden_hits: list[str] = []
    scaffolding_hits: list[str] = []
    leak_hits: list[str] = []
    jargon_hits: list[str] = []
    readability_flags: list[str] = []
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
        for label, pat in forbidden_patterns.items():
            m = pat.search(unquoted_body)
            if m:
                forbidden_hits.append(f"- `{ch.name}`: forbidden pattern `{label}` (`{m.group(0)}`)")

        # Anti-leakage checks on body prose above ## Notes
        for leak_label, leak_pat in anti_leakage_patterns.items():
            for m in leak_pat.finditer(body_before_notes):
                leak_hits.append(f"- `{ch.name}`: anti-leakage violation `{leak_label}` (`{m.group(0)}`)")

        # Jargon-to-notes check on body prose above ## Notes
        ch_jargon_found: list[str] = []
        body_lower = body_before_notes.lower()
        for term, plain_replacement in jargon_dict.items():
            if term.lower() in body_lower:
                ch_jargon_found.append(term)
                jargon_hits.append(
                    f"- `{ch.name}`: clinical term `{term}` in body prose → relocate to `## Notes` (use plain alternative: *{plain_replacement}*)"
                )

        # Readability metrics on body prose above ## Notes
        rm = compute_readability_metrics(body_before_notes, language=language)
        if language == "es":
            szig = float(rm["szigriszt"])
            avg_s = float(rm["avg_sentence_words"])
            long_40 = int(rm["long_sentences_over_35"])
            status_badge = "PASS (Bestseller)" if (szig >= szigriszt_min and avg_s <= max_avg_sentence_words and not ch_jargon_found) else "NEEDS SIMPLIFICATION"
            if szig < szigriszt_min or avg_s > max_avg_sentence_words:
                readability_flags.append(
                    f"- `{ch.name}`: Szigriszt `{szig}` (target ≥ {szigriszt_min}), Avg Sentence `{avg_s}w` (target ≤ {max_avg_sentence_words}w), >40w sentences: `{long_40}`"
                )
            readability_rows.append(
                f"| `{ch.name}` | {szig:.1f} | {avg_s:.1f}w | {long_40} | {len(ch_jargon_found)} | {status_badge} |"
            )
        else:
            fk = float(rm["fk_grade"])
            avg_s = float(rm["avg_sentence_words"])
            long_35 = int(rm["long_sentences_over_35"])
            status_badge = "PASS (Bestseller)" if (fk <= max_fk_grade and avg_s <= max_avg_sentence_words and not ch_jargon_found) else "NEEDS SIMPLIFICATION"
            if fk > max_fk_grade or avg_s > max_avg_sentence_words:
                readability_flags.append(
                    f"- `{ch.name}`: FK Grade `{fk}` (target ≤ {max_fk_grade}), Avg Sentence `{avg_s}w` (target ≤ {max_avg_sentence_words}w), >35w sentences: `{long_35}`"
                )
            readability_rows.append(
                f"| `{ch.name}` | {fk:.1f} | {avg_s:.1f}w | {long_35} | {len(ch_jargon_found)} | {status_badge} |"
            )

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

    bib_path = None
    for cand in (
        book_path / "research" / "sources.bib",
        book_path / "sources.bib",
        book_path.parent / "sources.bib",
        book_path.parent.parent / "sources.bib",
    ):
        if cand.is_file():
            bib_path = cand
            break
    bib_entries = 0
    if bib_path and bib_path.is_file():
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

    readability_header = (
        f"| Chapter | Szigriszt (≥{szigriszt_min:.1f}) | Avg Sent (≤{max_avg_sentence_words:.1f}w) | Sent >40w | Jargon Hits | Bestseller Gate |"
        if language == "es"
        else f"| Chapter | FK Grade (≤{max_fk_grade:.1f}) | Avg Sent (≤{max_avg_sentence_words:.1f}w) | Sent >35w | Jargon Hits | Bestseller Gate |"
    )

    lines.extend(
        [
            "",
            f"## 6. Readability, Jargon-to-Notes & Anti-Leakage Audit (`ARC-71` / `ARC-72` / `ARC-76` — Body Prose Above `## Notes`)",
            readability_header,
            "| :--- | ---: | ---: | ---: | ---: | :--- |",
            *readability_rows,
            "",
            "### 6a. Anti-Leakage Gate (No Inline `.md` Filenames, Backticked Footnotes, or Harness Meta-Phrases)",
        ]
    )
    if leak_hits:
        lines.extend(leak_hits)
    else:
        lines.append("- **Pass:** Zero `.md` filename leaks, backticked footnotes, or internal harness phrases in body prose.")

    lines.extend(["", "### 6b. Clinical Jargon Relocation Queue (`style/jargon-to-notes.yml`)"])
    if jargon_hits:
        lines.extend(jargon_hits)
    else:
        lines.append("- **Pass:** Zero clinical jargon violations in body prose (100% isolated in `## Notes`).")

    if char_mentions:
        lines.extend(
            [
                "",
                "## 7. Character Continuity Map (`characters.md`)",
                "| Character | First Mention | Chapters Appearing |",
                "| :--- | :--- | :--- |",
            ]
        )
        for full_name, _ in characters:
            chs = char_mentions.get(full_name, [])
            if chs:
                lines.append(f"| {full_name} | Ch.{chs[0]} | {', '.join(f'Ch.{c}' for c in chs)} |")

    lines.extend(["", "## 8. Residual Fact-Check Action Items (`research/fact-checks/*.md`)"])
    if open_fc_items:
        lines.extend(open_fc_items)
    else:
        lines.append("- **Pass:** No unchecked items in `research/fact-checks/`.")

    if use_gemini:
        lines.extend(["", "## 9. Long-Context Gemini 2.5 Pro Editorial Review", ""])
        lines.append(run_gemini_review(root, book_path, chapters))

    strict_ok = (
        not metaphor_collisions
        and not fn_issues
        and not forbidden_hits
        and not scaffolding_hits
        and not leak_hits
        and not ec_failures
        and citation_needed_total == 0
    )
    if bestseller_strict:
        strict_ok = strict_ok and not jargon_hits and not readability_flags

    return "\n".join(lines) + "\n", strict_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a book manuscript for continuity, metaphors, OKF cards, readability, and citations.")
    parser.add_argument("book", type=Path, help="Book or series directory (e.g. series/architectures-of-memory/book-01-vanishing-signal or series/parenthood-atlas)")
    parser.add_argument("--output", type=Path, default=None, help="Optional file path to write markdown report")
    parser.add_argument("--gemini", action="store_true", help="Run long-context Gemini 2.5 Pro holistic review")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any core audit or anti-leakage gate fails")
    parser.add_argument("--bestseller-strict", action="store_true", help="Also fail if any chapter exceeds FK Grade 10.5 or contains body jargon")
    args = parser.parse_args()

    root = repo_root()
    book_path = resolve_book_path(root, args.book)
    if not book_path.is_dir():
        print(f"error: directory not found: {book_path}", file=sys.stderr)
        sys.exit(1)

    report, strict_ok = audit_book(book_path, use_gemini=args.gemini, bestseller_strict=args.bestseller_strict)
    if args.output:
        out_path = args.output.resolve() if args.output.is_absolute() else (root / args.output).resolve()
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote audit report to {out_path}")
    else:
        sys.stdout.buffer.write(report.encode("utf-8"))

    if (args.strict or args.bestseller_strict) and not strict_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
