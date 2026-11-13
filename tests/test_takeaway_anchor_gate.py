"""Tests for the Stage 3 Takeaway box (<aside>) numeric anchor gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_manuscript import audit_takeaway_numeric_anchors  # noqa: E402


def test_anchored_numbers_pass_across_locales() -> None:
    en_doc = """
## I. Grounding Evidence

Take `400` micrograms daily (or `4` to `5` mg for high-risk recurrences) across `13,557` tracked youths;
absolute unaffected rates remain `96` to `98` percent with pooled `RR 0.31`.

<aside class="chapter-takeaway">
### Chapter 1 Takeaways: Core Anchors

- Standard dose is 400 micrograms, reserving 4–5 mg for clinical high-risk cases (see Chapters 2 and 14).
- Absolute unaffected births exceed 96–98% across cohorts of 13,557 adolescents (RR 0.31).
</aside>
"""
    assert audit_takeaway_numeric_anchors(en_doc, "01-en.md", language="en") == []

    es_doc = """
## I. Base empírica

El análisis siguió a 13.557 jóvenes y mostró una razón de riesgo de 0,31 y un cambio verbal de +1,4.

<aside class="chapter-takeaway">
### Conclusiones del Capítulo 3

- En 13 557 participantes (RR 0,31), la diferencia verbal fue de 1,4 puntos (véase capítulo 2).
</aside>
"""
    assert audit_takeaway_numeric_anchors(es_doc, "03-es.md", language="es") == []

    fr_doc = """
## I. Synthèse

La cohorte réunit 13\u202f557 adolescents avec un écart verbal de +1,4 point.

<aside class="chapter-takeaway">
### Retenir l'essentiel — Chapitre 3

- Sur 13 557 jeunes suivis, l'écart moyen demeure de 1,4 point (voir chapitre 2).
</aside>
"""
    assert audit_takeaway_numeric_anchors(fr_doc, "03-fr.md", language="fr") == []


def test_unanchored_aside_number_flagged_and_deduplicated() -> None:
    doc = """
## I. Risk Modeling

Maternal age past 35 changes cycle fertility, while 400 micrograms covers neural-tube synthesis.

<aside class="chapter-takeaway">
### Chapter 1 Takeaways

- Paternal age past 45 elevates relative risk despite >95% remaining unaffected.
- Avoid alarms before 45.
</aside>
"""
    errs = audit_takeaway_numeric_anchors(doc, "01-orphan.md", language="en")
    assert len(errs) == 2
    assert any("`45`" in e for e in errs)
    assert any("`95`" in e for e in errs)


def test_anchored_in_notes_passes() -> None:
    doc = """
## I. Body Prose

Cochrane meta-analysis confirms first-occurrence folate protection.[^ch01-folate]

<aside class="chapter-takeaway">
### Chapter 1 Takeaways

- Pooled review across 6,708 births yields RR 0.31.
</aside>

## Notes

[^ch01-folate]: De-Regil et al. (2015, Cochrane), 6,708 births, RR 0.31.
"""
    assert audit_takeaway_numeric_anchors(doc, "01-notes.md", language="en") == []


def test_biochemical_identifiers_and_ordinals_excluded() -> None:
    doc = """
## I. Body Prose

Enzymatic conversion trims maternal glucocorticoids before reaching fetal circulation.

<aside class="chapter-takeaway">
### Chapter 1 Takeaways

- Placental 11β-HSD2 buffering, vitamin B12, omega-3 intake, COVID-19 stress, and 2nd-trimester checks remain distinct.
</aside>
"""
    assert audit_takeaway_numeric_anchors(doc, "01-ids.md", language="en") == []


def test_no_aside_returns_empty() -> None:
    assert audit_takeaway_numeric_anchors("Plain text without aside.", "00.md", language="en") == []
