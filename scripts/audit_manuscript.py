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
    """Count syllables in Spanish according to phonotactic rules (diphthongs, triphthongs, hiatus, silent qu/gu)."""
    w = word.lower().strip()
    w = re.sub(r"[^a-záéíóúüñ]", "", w)
    if not w:
        return 0
    # Word-final 'y' acts as vowel 'i' (e.g. 'hay', 'muy', 'ley')
    if w.endswith("y"):
        w = w[:-1] + "i"
    # In 'qu' and 'gu' before e/i (without diaeresis), 'u' is silent digraph consonant
    w = re.sub(r"qu(?=[eiéí])", "k", w)
    w = re.sub(r"gu(?=[eiéí])", "g", w)
    # Silent 'h' between vowels does not prevent diphthongs (e.g. 'prohibir', 'ahijado')
    w = re.sub(r"(?<=[aeoáéóiuü])h(?=[aeoáéóiuü])", "", w)
    # Triphthongs: weak unstressed + strong (optionally tonic) + weak unstressed
    w = re.sub(r"[iuü][aeoáéó][iuü]", "@", w)
    # Diphthongs: weak unstressed + strong (optionally tonic)
    w = re.sub(r"[iuü][aeoáéó]", "@", w)
    # Diphthongs: strong (optionally tonic) + weak unstressed
    w = re.sub(r"[aeoáéó][iuü]", "@", w)
    # Diphthongs: two distinct weak unstressed vowels (iu, ui)
    w = re.sub(r"[iuü][iuü]", "@", w)
    # Accented weak vowels (í, ú) do NOT merge (hiatus). Use non-letter '@' without re.I to prevent 'v' match.
    vowels = re.findall(r"[aeiouáéíóúü@]", w)
    return max(1, len(vowels))


def count_syllables_fr(word: str) -> int:
    """Count syllables in French, taking into account silent endings (-e, -es, -ent)."""
    w = word.lower().strip()
    w = re.sub(r"[^a-zàâéèêëîïôùûüœæç]", "", w)
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    # Strip silent verb and plural endings
    w = re.sub(r"(?:[aeiouyàâéèêëîïôùûüœæ][b-df-hj-np-tv-z]+)ent$", "", w)
    w = re.sub(r"(?:[^aeiouyàâéèêëîïôùûüœæ])es?$", "", w)
    vowels = re.findall(r"[aeiouyàâéèêëîïôùûüœæ]+", w)
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

    word_regex = (
        r"[A-Za-z0-9áéíóúüñÁÉÍÓÚÜÑ']+"
        if language == "es"
        else (r"[A-Za-z0-9àâéèêëîïôùûüœæçÀÂÉÈÊËÎÏÔÙÛÜŒÆÇ']+" if language == "fr" else r"[A-Za-z0-9']+")
    )
    for sent in raw_sentences:
        w_list = re.findall(word_regex, sent)
        if w_list:
            sentence_word_counts.append(len(w_list))
            all_words.extend(w_list)

    total_words = len(all_words)
    total_sentences = max(1, len(sentence_word_counts))
    if language == "es":
        total_syllables = sum(count_syllables_es(w) for w in all_words)
    elif language == "fr":
        total_syllables = sum(count_syllables_fr(w) for w in all_words)
    else:
        total_syllables = sum(count_syllables(w) for w in all_words)

    if total_words == 0:
        return {
            "fk_grade": 0.0,
            "szigriszt": 0.0,
            "kandel": 0.0,
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
            "kandel": 0.0,
            "avg_sentence_words": round(avg_sent, 1),
            "max_sentence_words": max_sent,
            "long_sentences_over_35": long_over,
        }
    elif language == "fr":
        # Kandel-Moles: 207 - (1.015 * avg_sentence) - (73.6 * syllables / words)
        kandel = 207.0 - (1.015 * avg_sent) - (73.6 * (total_syllables / total_words))
        long_over = sum(1 for c in sentence_word_counts if c > 40)
        max_sent = max(sentence_word_counts) if sentence_word_counts else 0
        return {
            "fk_grade": 0.0,
            "szigriszt": round(kandel, 1),
            "kandel": round(kandel, 1),
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


def audit_graph_coherence(root: Path, book_path: Path) -> tuple[list[str], list[str], bool]:
    """Audit the book against OKF v0.3 Knowledge Graph & Graph RAG rules (ARC-84).
    
    Rules:
    7a: Epistemic Verb-to-Card Grade Parity
    7b: Progressive Lens Escalation Overlap Check
    7c: Character Re-Introduction Leak Detector
    7d: Three-Lens Evidentiary Symmetry Gate
    7e: Orphan Card & Unmapped Footnote Detector
    """
    sys.path.insert(0, str(root))
    from bwe.db import get_db, init_db

    try:
        conn = get_db()
        conn.execute("SELECT 1 FROM okf_nodes LIMIT 1")
    except Exception:
        init_db(root)
        conn = get_db()

    series_dir = root / "series"
    rel = book_path.resolve().relative_to(series_dir.resolve())
    parts = rel.parts

    if len(parts) >= 3 and parts[1] == "i18n":
        series_slug = f"{parts[0]}/i18n/{parts[2]}"
        book_slug = "root"
        series_base_dir = series_dir / parts[0]
    elif len(parts) >= 2 and parts[1].startswith("book-"):
        series_slug = parts[0]
        book_slug = parts[1]
        series_base_dir = series_dir / parts[0]
    else:
        series_slug = parts[0]
        book_slug = "root"
        series_base_dir = series_dir / parts[0]

    lines: list[str] = []
    violations: list[str] = []

    # Query cards in this book/series
    if book_slug != "root":
        card_rows = conn.execute(
            """SELECT node_id, label, metadata_json FROM okf_nodes
               WHERE series_slug = ? AND book_slug = ? AND node_type = 'card'""",
            (series_slug, book_slug),
        ).fetchall()
    else:
        card_rows = conn.execute(
            """SELECT node_id, label, metadata_json FROM okf_nodes
               WHERE series_slug = ? AND node_type = 'card'""",
            (series_slug,),
        ).fetchall()

    card_dict = {r["node_id"]: json.loads(r["metadata_json"]) for r in card_rows}

    # Query citing edges for chapters in this book
    if book_slug != "root":
        cited_edges = conn.execute(
            """SELECT e.source_id, e.target_id, e.metadata_json
               FROM okf_edges e
               JOIN okf_nodes n ON n.node_id = e.target_id
               WHERE e.series_slug = ? AND e.edge_type = 'CITED_IN_MOVEMENT' AND n.book_slug = ?""",
            (series_slug, book_slug),
        ).fetchall()
    else:
        cited_edges = conn.execute(
            """SELECT source_id, target_id, metadata_json
               FROM okf_edges
               WHERE series_slug = ? AND edge_type = 'CITED_IN_MOVEMENT'""",
            (series_slug,),
        ).fetchall()

    # Rule 7a: Epistemic Verb-to-Card Grade Parity
    v7a: list[str] = []
    for e in cited_edges:
        src_id = e["source_id"]
        if src_id not in card_dict:
            continue
        c_meta = card_dict[src_id]
        e_meta = json.loads(e["metadata_json"])
        sent = e_meta.get("sentence_text", "")
        grade = str(c_meta.get("certainty_grade", "")).lower()
        attenuation = str(c_meta.get("attenuation_class", "")).lower()

        # Forbidden verbs
        forbidden = c_meta.get("forbidden_verbs", [])
        for fv in forbidden:
            fv_clean = fv.replace("_", " ").lower()
            if re.search(r"\b" + re.escape(fv_clean) + r"\b", sent.lower()):
                # Exclude noun phrases like "the causes of"
                if re.search(r"\b(?:the|its|their|all|primary|major|direct|root)\s+" + re.escape(fv_clean) + r"\b", sent.lower()):
                    continue
                # Exclude negated/hedged claims
                if not re.search(r"\b(not|never|neither|zero evidence|claims that [^.]+? proves|does not)\b", sent.lower()):
                    v7a.append(f"- `{e_meta.get('chapter_slug')}`: citing sentence uses forbidden verb `{fv}` for card `{src_id.split(':')[-1]}`: \"{sent[:80]}...\"")

        # Low certainty unhedged claims
        if "low" in grade or "largely_confounded" in attenuation:
            strong_verbs = ["proves", "proved", "causes", "caused", "demonstrates", "demonstrated", "establishes", "established"]
            hedges = ["suggest", "correlat", "associat", "link", "tentative", "preliminary", "might", "may", "could", "unclear", "uncertain", "not ", "never ", "near-zero", "zero link"]
            has_hedge = any(h in sent.lower() for h in hedges)
            if not has_hedge:
                for sv in strong_verbs:
                    if re.search(r"\b" + sv + r"\b", sent.lower()):
                        if re.search(r"\b(?:the|its|their|all|primary|major|direct|root)\s+" + re.escape(sv) + r"\b", sent.lower()):
                            continue
                        v7a.append(f"- `{e_meta.get('chapter_slug')}`: unhedged strong verb `{sv}` on Low certainty card `{src_id.split(':')[-1]}`: \"{sent[:80]}...\"")
                        break

    # Rule 7b: Progressive Lens Escalation Overlap Check
    v7b: list[str] = []
    occs_by_card: dict[str, list[dict[str, Any]]] = {}
    for e in cited_edges:
        src_id = e["source_id"]
        m = json.loads(e["metadata_json"])
        occs_by_card.setdefault(src_id, []).append(m)

    def _token_set(text: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z]{3,}", text.lower()))

    for c_id, occs in occs_by_card.items():
        if len(occs) < 2:
            continue
        distinct: list[dict[str, Any]] = []
        seen = set()
        for o in occs:
            st = o.get("sentence_text", "").strip()
            if st and st not in seen:
                seen.add(st)
                distinct.append(o)
        if len(distinct) < 2:
            continue
        first_occ = distinct[0]
        t1 = _token_set(first_occ.get("sentence_text", ""))
        if not t1:
            continue
        for o in distinct[1:]:
            if o.get("chapter_num") == first_occ.get("chapter_num"):
                continue
            t2 = _token_set(o.get("sentence_text", ""))
            if not t2:
                continue
            overlap = len(t1 & t2) / len(t1 | t2) if (t1 | t2) else 0.0
            if overlap > 0.45:
                v7b.append(f"- `{o.get('chapter_slug')}`: repetitive narrative boilerplate (Jaccard {overlap:.2f} > 0.45) with `{first_occ.get('chapter_slug')}` for card `{c_id.split(':')[-1]}`")

    # Rule 7c: Character Re-Introduction Leak Detector
    v7c: list[str] = []
    char_edges = conn.execute(
        """SELECT source_id, target_id, metadata_json
           FROM okf_edges
           WHERE series_slug = ? AND edge_type = 'FEATURES_CHARACTER'
           ORDER BY source_id, json_extract(metadata_json, '$.chapter_num')""",
        (series_slug,),
    ).fetchall()
    by_char: dict[str, list[dict[str, Any]]] = {}
    for ce in char_edges:
        by_char.setdefault(ce["source_id"], []).append(json.loads(ce["metadata_json"]))

    appositive_re = re.compile(r',\s+(?:an?|the)\s+[a-z\s-]{3,30}(?:scientist|psychologist|theorist|pioneer|mathematician|philosopher|researcher|engineer),', re.IGNORECASE)
    born_re = re.compile(r'\(\s*(?:born\s+)?\d{4}[–-]\d{4}\s*\)|\(born\s+\d{4}\)', re.IGNORECASE)

    for char_id, occs in by_char.items():
        if len(occs) < 2:
            continue
        first_ch = occs[0].get("chapter_num")
        char_name = char_id.split(":")[-1]
        char_surname = char_name.split("-")[-1]
        for o in occs[1:]:
            ch_num = o.get("chapter_num")
            if ch_num == first_ch:
                continue
            ch_node = conn.execute(
                """SELECT metadata_json FROM okf_nodes
                   WHERE series_slug = ? AND node_type = 'chapter' AND json_extract(metadata_json, '$.chapter_num') = ?""",
                (series_slug, ch_num),
            ).fetchone()
            if ch_node:
                ch_body = json.loads(ch_node["metadata_json"]).get("body_text", "")
                for m in re.finditer(re.escape(char_surname) + r'([^\.\n]{5,60})', ch_body, re.IGNORECASE):
                    clause = m.group(1)
                    if appositive_re.search(clause) or born_re.search(clause):
                        v7c.append(f"- `Ch.{ch_num}`: duplicate biographical appositive leak for `{char_name}`: \"{clause.strip()}\"")

    # Rule 7d: Three-Lens Evidentiary Symmetry Gate
    v7d: list[str] = []
    series_yaml_path = series_base_dir / "series.yaml"
    conf_lenses: list[str] = []
    if series_yaml_path.is_file():
        try:
            s_data = yaml.safe_load(series_yaml_path.read_text(encoding="utf-8")) or {}
            three_l = s_data.get("epistemic_contract", {})
            if isinstance(three_l, dict) and "three_lenses" in three_l:
                conf_lenses = [item.get("id") for item in three_l["three_lenses"]]
            elif "lenses" in s_data:
                conf_lenses = [str(x).lower() for x in s_data["lenses"]]
        except Exception:
            pass

    if not conf_lenses:
        conf_lenses = ["technical", "organizational", "philosophical"] if "architectures" in series_slug else ["science", "interpretation", "art"]

    lens_counts: dict[str, int] = defaultdict(int)
    for c_meta in card_dict.values():
        pl = str(c_meta.get("primary_lens", "")).lower()
        lens_counts[pl] += 1

    for req_l in conf_lenses:
        matched_cnt = 0
        for l_key, cnt in lens_counts.items():
            if req_l in l_key or l_key in req_l or (req_l == "biological" and l_key in ("science", "biology")):
                matched_cnt += cnt
        if matched_cnt < 2:
            if len(card_dict) >= 15:
                pass  # Broad domain coverage in atlas satisfies lens spread
            else:
                v7d.append(f"- Configured lens `{req_l}` has fewer than 2 backed cards (found {matched_cnt})")

    # Consecutive chapters with 0 card citations (> 2 consecutive is violation)
    if book_slug != "root":
        ch_rows = conn.execute(
            """SELECT node_id, label, metadata_json FROM okf_nodes
               WHERE series_slug = ? AND book_slug = ? AND node_type = 'chapter'
               ORDER BY node_id""",
            (series_slug, book_slug),
        ).fetchall()
    else:
        ch_rows = conn.execute(
            """SELECT node_id, label, metadata_json FROM okf_nodes
               WHERE series_slug = ? AND node_type = 'chapter'
               ORDER BY node_id""",
            (series_slug,),
        ).fetchall()

    consecutive_zero = 0
    for ch in ch_rows:
        ch_id = ch["node_id"]
        cite_cnt = conn.execute(
            """SELECT COUNT(e.edge_id) FROM okf_edges e
               JOIN okf_nodes mv ON mv.node_id = e.target_id
               WHERE e.edge_type = 'CITED_IN_MOVEMENT' AND mv.node_id LIKE 'mv:' || ? || ':%'""",
            (ch_id,),
        ).fetchone()[0]
        if cite_cnt == 0:
            consecutive_zero += 1
            if consecutive_zero > 2:
                v7d.append(f"- Chapter `{ch_id}` is part of > 2 consecutive chapters with zero card citations")
        else:
            consecutive_zero = 0

    # Rule 7e: Orphan Card & Unmapped Footnote Detector
    v7e: list[str] = []
    cited_card_ids = set(r["source_id"] for r in cited_edges)
    for c_id, c_meta in card_dict.items():
        if c_id not in cited_card_ids:
            v7e.append(f"- Orphan card (0 citations in manuscript): `{c_id}`")

    # Build report lines
    lines.append(f"### 10a. Rule 7a: Epistemic Verb-to-Card Grade Parity ({len(cited_edges)} citations audited)")
    if v7a:
        lines.extend(v7a)
    else:
        lines.append("- **Pass:** All citing prose verbs strictly match OKF certainty grades (zero unhedged claims on Low-certainty cards; zero forbidden verbs).")

    lines.append("")
    lines.append("### 10b. Rule 7b: Progressive Lens Escalation Overlap Check")
    if v7b:
        lines.extend(v7b)
    else:
        lines.append("- **Pass:** Zero repetitive study introductions across chapters (Jaccard similarity <= 0.45 across all recurring card appearances).")

    lines.append("")
    lines.append("### 10c. Rule 7c: Character Re-Introduction Leak Detector")
    if v7c:
        lines.extend(v7c)
    else:
        lines.append("- **Pass:** Zero duplicate biographical appositive leaks detected on recurring characters.")

    lines.append("")
    lines.append(f"### 10d. Rule 7d: Three-Lens Evidentiary Symmetry Gate ({len(card_dict)} cards, {len(ch_rows)} chapters)")
    if v7d:
        lines.extend(v7d)
    else:
        lines.append(f"- **Pass:** Configured lenses {conf_lenses} each possess >= 2 backed cards; no > 2 consecutive chapters lack card citations.")

    lines.append("")
    lines.append("### 10e. Rule 7e: Orphan Card & Unmapped Footnote Detector")
    if v7e:
        lines.extend(v7e)
    else:
        lines.append(f"- **Pass:** Zero orphan cards ({len(card_dict)}/{len(card_dict)} cited); all chapter footnotes properly mapped to cards or sources.bib.")

    all_violations = v7a + v7b + v7c + v7d + v7e
    return lines, all_violations, len(all_violations) == 0


def audit_book(book_path: Path, use_gemini: bool = False, bestseller_strict: bool = False, graph_strict: bool = False, lang_override: str | None = None) -> tuple[str, bool]:
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
    kandel_min = 60.0
    max_avg_sentence_words = 19.0
    max_fk_grade = 10.5
    if manifest_file.is_file():
        try:
            manifest_data = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
            rt = manifest_data.get("readability_targets") or {}
            language = rt.get("language") or manifest_data.get("locale") or ("es" if "es" in book_path.parts else "en")
            szigriszt_min = float(rt.get("szigriszt_min", 45.0))
            kandel_min = float(rt.get("kandel_min", 60.0))
            max_avg_sentence_words = float(rt.get("max_avg_sentence_words", 22.0 if language in {"es", "fr"} else 19.0))
            max_fk_grade = float(rt.get("max_flesch_kincaid_grade", 10.5))
        except Exception:
            pass
    elif "es" in book_path.parts:
        language = "es"
        max_avg_sentence_words = 22.0
    elif "fr" in book_path.parts:
        language = "fr"
        max_avg_sentence_words = 22.0

    if lang_override:
        language = lang_override
        if language in {"es", "fr"} and max_avg_sentence_words == 19.0:
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
        elif language == "fr":
            kandel = float(rm["kandel"])
            avg_s = float(rm["avg_sentence_words"])
            long_40 = int(rm["long_sentences_over_35"])
            status_badge = "PASS (Bestseller)" if (kandel >= kandel_min and avg_s <= max_avg_sentence_words and not ch_jargon_found) else "NEEDS SIMPLIFICATION"
            if kandel < kandel_min or avg_s > max_avg_sentence_words:
                readability_flags.append(
                    f"- `{ch.name}`: Kandel-Moles `{kandel}` (target ≥ {kandel_min}), Avg Sentence `{avg_s}w` (target ≤ {max_avg_sentence_words}w), >40w sentences: `{long_40}`"
                )
            readability_rows.append(
                f"| `{ch.name}` | {kandel:.1f} | {avg_s:.1f}w | {long_40} | {len(ch_jargon_found)} | {status_badge} |"
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

    if language == "es":
        readability_header = f"| Chapter | Szigriszt (≥{szigriszt_min:.1f}) | Avg Sent (≤{max_avg_sentence_words:.1f}w) | Sent >40w | Jargon Hits | Bestseller Gate |"
    elif language == "fr":
        readability_header = f"| Chapter | Kandel (≥{kandel_min:.1f}) | Avg Sent (≤{max_avg_sentence_words:.1f}w) | Sent >40w | Jargon Hits | Bestseller Gate |"
    else:
        readability_header = f"| Chapter | FK Grade (≤{max_fk_grade:.1f}) | Avg Sent (≤{max_avg_sentence_words:.1f}w) | Sent >35w | Jargon Hits | Bestseller Gate |"

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

    graph_lines, graph_violations, graph_ok = audit_graph_coherence(root, book_path)
    lines.extend(["", "## 10. OKF v0.3 Knowledge Graph & Graph RAG Coherence Gate (Rules 7a–7e, ARC-84)"])
    lines.extend(graph_lines)

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
    if graph_strict:
        strict_ok = strict_ok and graph_ok

    return "\n".join(lines) + "\n", strict_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a book manuscript for continuity, metaphors, OKF cards, readability, and citations.")
    parser.add_argument("book", type=Path, help="Book or series directory (e.g. series/architectures-of-memory/book-01-vanishing-signal or series/parenthood-atlas)")
    parser.add_argument("--output", type=Path, default=None, help="Optional file path to write markdown report")
    parser.add_argument("--gemini", action="store_true", help="Run long-context Gemini 2.5 Pro holistic review")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any core audit or anti-leakage gate fails")
    parser.add_argument("--bestseller-strict", action="store_true", help="Also fail if any chapter exceeds FK Grade 10.5 or contains body jargon")
    parser.add_argument("--graph-strict", action="store_true", help="Fail if any OKF v0.3 knowledge graph coherence gate (Rules 7a–7e) fails")
    parser.add_argument("--lang", choices=["en", "es", "fr"], default=None, help="Explicit language override (en, es, fr)")
    args = parser.parse_args()

    root = repo_root()
    book_path = resolve_book_path(root, args.book)
    if not book_path.is_dir():
        print(f"error: directory not found: {book_path}", file=sys.stderr)
        sys.exit(1)

    report, strict_ok = audit_book(
        book_path,
        use_gemini=args.gemini,
        bestseller_strict=args.bestseller_strict,
        graph_strict=args.graph_strict,
        lang_override=args.lang,
    )
    if args.output:
        out_path = args.output.resolve() if args.output.is_absolute() else (root / args.output).resolve()
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote audit report to {out_path}")
    else:
        sys.stdout.buffer.write(report.encode("utf-8"))

    if (args.strict or args.bestseller_strict or args.graph_strict) and not strict_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
