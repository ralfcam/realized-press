"""bwe/style_sculptor.py: SotA LLM Frozen-Skeleton Style Sculptor & Verification Harness (BWE v1.3.1, ARC-104).

Implements the 3-stage Frozen-Skeleton Phrasal-Sculpting Pipeline:
- Stage 1 (`extract_epistemic_skeleton`): Extracts and freezes all inline footnote keys (`[^...]`),
  bold epistemic claim verbs (`**shows**`, `**suggests**`, `**is associated with**`), quantitative
  effect-size tokens (`N = ...`, `RR = ...`, percentages, years), and italicized conceptual anchors.
- Stage 2 (`build_sculptor_prompt`): Synthesizes a constrained phrasal-sculpting prompt with kinetic
  Anglo-Saxon verb palettes (`style/phrasal-poetics.yml`), active movement metaphors from OKF v0.3
  Evidence Cards, and asymmetric cadence targets (periodic setup + 5-9 word aphoristic hinge).
- Stage 3 (`verify_sculpted_candidate`): Mechanically verifies that a sculpted replacement preserves
  100% of frozen epistemic tokens while passing Rules 8a-8e (`audit_micro_qa` + `compute_phrasal_poetics`).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from audit_manuscript import (
    INLINE_FN_RE,
    audit_micro_qa,
    compute_phrasal_poetics,
    compute_readability_metrics,
    load_phrasal_poetics_spec,
)

EPISTEMIC_VERB_RE = re.compile(
    r"\*\*(?:shows|show|suggests|suggest|is\s+associated\s+with|are\s+associated\s+with|"
    r"muestra|muestran|sugiere|sugieren|se\s+asocia\s+con|se\s+asocian\s+con)\*\*",
    re.IGNORECASE,
)

QUANT_TOKEN_RE = re.compile(
    r"(?:\b(?:N|RR|OR|HR|d|r)\s*=\s*[0-9][0-9.,–\-]*|\b\d+(?:\.\d+)?%|\b\.[0-9]{2}\b|\b(?:19|20)\d{2}s?\b)"
)

ITALIC_ANCHOR_RE = re.compile(r"(?<!\*)\*([^*]{3,45})\*(?!\*)")


@dataclass
class EpistemicSkeleton:
    """Frozen invariants that must survive phrasal sculpting unchanged."""

    footnotes: list[str] = field(default_factory=list)
    epistemic_verbs: list[str] = field(default_factory=list)
    quantitative_tokens: list[str] = field(default_factory=list)
    italicized_anchors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_epistemic_skeleton(paragraph_text: str, language: str = "en") -> EpistemicSkeleton:
    """Stage 1: Extract frozen citations, epistemic verbs, quantitative tokens, and italicized anchors."""
    footnotes = [f"[^{fn}]" for fn in INLINE_FN_RE.findall(paragraph_text)]
    epistemic_verbs = [m.group(0) for m in EPISTEMIC_VERB_RE.finditer(paragraph_text)]
    quantitative_tokens = []
    for m in QUANT_TOKEN_RE.finditer(paragraph_text):
        tok = m.group(0).strip()
        if tok not in quantitative_tokens:
            quantitative_tokens.append(tok)
    italicized_anchors = []
    for m in ITALIC_ANCHOR_RE.finditer(paragraph_text):
        anc = f"*{m.group(1).strip()}*"
        if anc not in italicized_anchors:
            italicized_anchors.append(anc)
    return EpistemicSkeleton(
        footnotes=footnotes,
        epistemic_verbs=epistemic_verbs,
        quantitative_tokens=quantitative_tokens,
        italicized_anchors=italicized_anchors,
    )


def build_sculptor_prompt(
    paragraph_text: str,
    section_title: str = "",
    canonical_metaphor: str = "",
    language: str = "en",
    reasons: list[str] | None = None,
) -> str:
    """Stage 2: Build a deterministic Frozen-Skeleton Phrasal-Sculpting prompt for an LLM or subagent."""
    skeleton = extract_epistemic_skeleton(paragraph_text, language=language)
    spec = load_phrasal_poetics_spec(REPO_ROOT, language=language)
    lexicon = spec.get("kinetic_verb_lexicon") or {}

    verb_palette_lines: list[str] = []
    for domain, vlist in lexicon.items():
        if isinstance(vlist, list) and vlist:
            verb_palette_lines.append(f"  - {domain}: {', '.join(str(v) for v in vlist[:12])}")

    diag_str = ", ".join(reasons) if reasons else "general phrasal elevation & cadence sharpening"
    metaphor_line = (
        f"- **Sustained Controlling Metaphor:** `{canonical_metaphor}` (derive verbs and concrete nouns from this physical domain; never mix conflicting metaphors in the same movement)."
        if canonical_metaphor
        else "- **Metaphor Discipline:** Use at most 1 physical controlling metaphor across the paragraph; derive verbs directly from that physical action."
    )

    lines = [
        "# Frozen-Skeleton Phrasal-Sculpting Task (BWE v1.3.1 — ARC-104)",
        f"- **Target Section:** `{section_title or 'Body Movement'}`",
        f"- **Diagnostic Trigger:** {diag_str}",
        "",
        "## 1. Frozen Epistemic Skeleton (100% Immutable — Must Appear Verbatim)",
        f"- **Inline Footnote Anchors:** {', '.join(f'`{f}`' for f in skeleton.footnotes) if skeleton.footnotes else '*(none)*'}",
        f"- **Locked Grade-Calibrated Epistemic Verbs:** {', '.join(f'`{v}`' for v in skeleton.epistemic_verbs) if skeleton.epistemic_verbs else '*(none)*'}",
        f"- **Quantitative & Temporal Tokens:** {', '.join(f'`{q}`' for q in skeleton.quantitative_tokens) if skeleton.quantitative_tokens else '*(none)*'}",
        f"- **Italicized Conceptual Anchors:** {', '.join(f'`{a}`' for a in skeleton.italicized_anchors) if skeleton.italicized_anchors else '*(none)*'}",
        "",
        "## 2. Five Phrasal-Sculpting Operations",
        "1. **Somatic & Kinetic Verbs over Copulas:** Replace weak state-of-being predicates (`is`, `are`, `has`, `becomes`, `provides`, `serves as`) with 1–2 syllable Anglo-Saxon kinetic verbs:",
        *verb_palette_lines,
        f"2. {metaphor_line}",
        "3. **Asymmetric Clausal Counterpoint & Aphoristic Hinge:** Vary sentence lengths (`σ ≥ 3.0w`): pair a 22–28 word periodic setup sentence with a crisp 5–9 word declarative hinge sentence separated by a period (`.`). Do NOT join independent clauses with semicolons (`;`) when a period creates a sharper hinge.",
        "4. **Zero Nominalization Clusters or Participial Tail-Drags:** Eliminate abstract `-tion/-ment/-ity` noun strings (`>2` per sentence) and delete formulaic LLM tail clauses (`, highlighting...`, `, underscoring...`, `, ensuring...`).",
        "5. **Micro-QA & Bestseller Readability Ceilings:** Every paragraph must be `≤ 135 words` and `≤ 6 sentences` (split into two paragraphs if needed, keeping each empirical study reference attached to its `[^...]` footnote), every sentence `≤ 35 words`, and local paragraph Flesch-Kincaid Grade `≤ 11.5`.",
        "",
        "## 3. Source Paragraph(s) to Sculpt",
        "```markdown",
        paragraph_text.strip(),
        "```",
    ]
    return "\n".join(lines) + "\n"


def verify_sculpted_candidate(
    original_text: str,
    candidate_text: str,
    language: str = "en",
    chapter_slug: str = "candidate.md",
) -> dict[str, Any]:
    """Stage 3: Verify that a sculpted paragraph/section preserves 100% of the epistemic skeleton and passes Rules 8a-8e."""
    orig_skel = extract_epistemic_skeleton(original_text, language=language)
    cand_skel = extract_epistemic_skeleton(candidate_text, language=language)

    missing_footnotes = [f for f in orig_skel.footnotes if f not in cand_skel.footnotes]
    orig_verbs_lower = [v.lower() for v in orig_skel.epistemic_verbs]
    cand_verbs_lower = [v.lower() for v in cand_skel.epistemic_verbs]
    missing_verbs = [v for v in orig_skel.epistemic_verbs if v.lower() not in cand_verbs_lower]
    missing_stats = [q for q in orig_skel.quantitative_tokens if q not in candidate_text]

    hard_errs, warnings, micro_metrics = audit_micro_qa(
        candidate_text,
        language=language,
        chapter_slug=chapter_slug,
    )
    poetics_before = compute_phrasal_poetics(original_text, language=language, chapter_slug=chapter_slug)
    poetics_after = compute_phrasal_poetics(candidate_text, language=language, chapter_slug=chapter_slug)
    rm_before = compute_readability_metrics(original_text, language=language)
    rm_after = compute_readability_metrics(candidate_text, language=language)

    passed = (
        not missing_footnotes
        and not missing_verbs
        and not missing_stats
        and not hard_errs
        and not warnings
        and not poetics_after["warnings"]
    )

    return {
        "passed": passed,
        "missing_footnotes": missing_footnotes,
        "missing_verbs": missing_verbs,
        "missing_stats": missing_stats,
        "micro_hard_errors": hard_errs,
        "micro_warnings": warnings,
        "poetics_warnings": poetics_after["warnings"],
        "poetics_score_before": poetics_before["chapter_poetics_score"],
        "poetics_score_after": poetics_after["chapter_poetics_score"],
        "copula_ratio_before": poetics_before["copula_ratio"],
        "copula_ratio_after": poetics_after["copula_ratio"],
        "fk_grade_before": rm_before.get("fk_grade", 0.0),
        "fk_grade_after": rm_after.get("fk_grade", 0.0),
        "micro_metrics": micro_metrics,
    }


def resolve_chapter_file(series_slug: str, chapter_slug: str, book_slug: str | None = None, lang: str = "en") -> tuple[Path, Path]:
    """Locate the book directory and markdown chapter file."""
    base = REPO_ROOT / "series" / series_slug
    if lang and lang != "en" and (base / "i18n" / lang).is_dir():
        book_dir = base / "i18n" / lang
    elif book_slug and (base / book_slug).is_dir():
        book_dir = base / book_slug
    else:
        book_dir = base

    chapters_dir = book_dir / "chapters"
    exact = chapters_dir / (chapter_slug if chapter_slug.endswith(".md") else f"{chapter_slug}.md")
    if exact.is_file():
        return book_dir, exact

    matches = sorted(chapters_dir.glob(f"{chapter_slug}*.md"))
    if matches:
        return book_dir, matches[0]
    raise FileNotFoundError(f"Chapter '{chapter_slug}' not found under {chapters_dir}")


def generate_chapter_sculpt_pack(
    series_slug: str,
    chapter_slug: str,
    book_slug: str | None = None,
    lang: str = "en",
    top_k: int = 5,
) -> dict[str, Any]:
    """Compile a complete Frozen-Skeleton Phrasal-Sculpting Pack for a chapter."""
    book_dir, ch_path = resolve_chapter_file(series_slug, chapter_slug, book_slug=book_slug, lang=lang)
    raw_md = ch_path.read_text(encoding="utf-8")
    body_before_notes = raw_md.split("## Notes")[0] if "## Notes" in raw_md else raw_md

    # Pull controlling metaphors from OKF v0.3 Chapter Context Pack if available
    canonical_metaphors: list[str] = []
    try:
        from bwe.graph_rag import compile_chapter_context_pack

        ccp = compile_chapter_context_pack(series_slug=series_slug, chapter_slug=ch_path.stem, book_slug=book_slug)
        for card in ccp.cited_cards:
            for m in card.get("canonical_metaphors") or []:
                if m and m not in canonical_metaphors:
                    canonical_metaphors.append(str(m))
    except Exception:
        pass

    hard_errs, micro_warns, micro_metrics = audit_micro_qa(
        body_before_notes,
        language=lang,
        chapter_slug=ch_path.name,
    )
    poetics = compute_phrasal_poetics(
        body_before_notes,
        language=lang,
        chapter_slug=ch_path.name,
        root=REPO_ROOT,
        book_path=book_dir,
    )

    primary_metaphor = canonical_metaphors[0] if canonical_metaphors else ""
    targets: list[dict[str, Any]] = []
    seen_indices: set[int] = set()

    # Include any paragraph flagged by Micro-QA or scoring < 85.0 in Phrasal Poetics
    para_warn_map: dict[int, list[str]] = {}
    for w in hard_errs + micro_warns + poetics["warnings"]:
        m_idx = re.search(r"\[p\.(\d+)", w)
        if m_idx:
            p_idx = int(m_idx.group(1))
            para_warn_map.setdefault(p_idx, []).append(w.split("]: ", 1)[-1])

    candidates = sorted(
        poetics["paragraphs"],
        key=lambda p: (
            0 if p["index"] in para_warn_map else 1,
            p["poetics_score"],
            -p["words"],
        ),
    )

    for p in candidates:
        p_idx = p["index"]
        if p_idx in seen_indices:
            continue
        reasons = list(para_warn_map.get(p_idx, [])) + list(p["reasons"])
        if not reasons and len(targets) >= top_k:
            continue
        if len(targets) >= top_k and p_idx not in para_warn_map:
            continue
        seen_indices.add(p_idx)
        skel = extract_epistemic_skeleton(p["raw_text"], language=lang)
        prompt = build_sculptor_prompt(
            p["raw_text"],
            section_title=p["section"],
            canonical_metaphor=primary_metaphor,
            language=lang,
            reasons=reasons,
        )
        targets.append(
            {
                "paragraph_index": p_idx,
                "section": p["section"],
                "words": p["words"],
                "sentences": p["sentences"],
                "poetics_score": p["poetics_score"],
                "copula_ratio": p["copula_ratio"],
                "cadence_sigma": p["cadence_sigma"],
                "reasons": reasons,
                "skeleton": skel.to_dict(),
                "sculpt_prompt": prompt,
            }
        )

    return {
        "series_slug": series_slug,
        "chapter_slug": ch_path.name,
        "language": lang,
        "chapter_poetics_score": poetics["chapter_poetics_score"],
        "copula_ratio": poetics["copula_ratio"],
        "nominalization_clusters": poetics["nominalization_clusters"],
        "participial_tail_drags": poetics["participial_tail_drags"],
        "negation_pivots": poetics["negation_pivots"],
        "avg_cadence_sigma": poetics["avg_cadence_sigma"],
        "micro_metrics": micro_metrics,
        "canonical_metaphors": canonical_metaphors[:5],
        "target_count": len(targets),
        "targets": targets,
    }
