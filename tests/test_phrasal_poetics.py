"""tests/test_phrasal_poetics.py: Unit and regression test suite for BWE v1.3.1 SotA LLM Phrasal Poetics Linter & Style Sculptor (ARC-104).

Tests:
1. Specification loader (`load_phrasal_poetics_spec`) for EN (`style/phrasal-poetics.yml`) and ES (`series/parenthood-atlas/i18n/es/style/phrasal-poetics.yml`).
2. Rule 8e (`compute_phrasal_poetics`):
   - Copula density vs. kinetic verb lexicon immunity & locked epistemic verb immunity.
   - Abstract nominalization cluster detection (>2 per sentence) vs. whitelist immunity.
   - Formulaic participial tail-drag detection (`, highlighting...`, `, underscoring...`).
   - Formulaic negation-pivot (`not merely X, but Y`) chapter cap.
   - Asymmetric cadence sigma & aphoristic hinge scoring.
3. Frozen-Skeleton Style Sculptor (`bwe/style_sculptor.py`):
   - Stage 1: `extract_epistemic_skeleton` (footnotes, bold claim verbs, quantitative tokens, italicized anchors).
   - Stage 2: `build_sculptor_prompt` generation.
   - Stage 3: `verify_sculpted_candidate` (rejects missing footnotes/verbs/stats; accepts kinetic sculpted replacements).
   - `generate_chapter_sculpt_pack` & CLI `sculpt --dry-run`.
4. FastAPI `/hx/micro-qa/{series_slug}/{chapter_slug}` Phrasal Poetics & Sculpt prompt integration.
"""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from audit_manuscript import compute_phrasal_poetics, load_phrasal_poetics_spec
from bwe.style_sculptor import (
    build_sculptor_prompt,
    extract_epistemic_skeleton,
    generate_chapter_sculpt_pack,
    verify_sculpted_candidate,
)


def test_load_phrasal_poetics_spec_en_and_es():
    spec_en = load_phrasal_poetics_spec(REPO_ROOT, language="en")
    assert spec_en["language"] == "en"
    assert "max_copula_ratio" in spec_en["thresholds"]
    assert "checkpoint_and_boundary" in spec_en["kinetic_verb_lexicon"]

    spec_es = load_phrasal_poetics_spec(REPO_ROOT, language="es")
    assert spec_es["language"] == "es"
    assert spec_es["thresholds"]["max_nominalizations_per_sentence"] == 3


def test_compute_phrasal_poetics_copula_vs_kinetic():
    flat_prose = (
        "## I. Movement\n\n"
        "The placenta is a barrier in the womb. "
        "The enzyme is present inside the tissue. "
        "Cortisol is a hormone that is active during stress. "
        "The effect is an important factor for the fetus.\n"
    )
    res_flat = compute_phrasal_poetics(flat_prose, language="en", chapter_slug="flat.md")
    assert res_flat["copula_ratio"] >= 0.75
    assert any("copula density" in w for w in res_flat["warnings"])

    kinetic_prose = (
        "## I. Movement\n\n"
        "Between mother and fetus stands a molecular customs officer that inspects every drop of blood. "
        "The enzyme disarms maternal stress hormones before they flood the fetal brain. "
        "Most surges stop cold at the gate.\n"
    )
    res_kinetic = compute_phrasal_poetics(kinetic_prose, language="en", chapter_slug="kinetic.md")
    assert res_kinetic["copula_ratio"] == 0.0
    assert res_kinetic["chapter_poetics_score"] > res_flat["chapter_poetics_score"]
    assert not res_kinetic["warnings"]


def test_compute_phrasal_poetics_nominalization_clusters_and_tail_drags():
    bloated_prose = (
        "## I. Movement\n\n"
        "The conceptualization of institutionalization and dysregulation necessitates reconceptualization, "
        "highlighting the overarching transformation of developmental trajectories.\n"
    )
    res = compute_phrasal_poetics(bloated_prose, language="en", chapter_slug="bloated.md")
    assert res["nominalization_clusters"] >= 1
    assert res["participial_tail_drags"] >= 1
    assert any("Abstract nominalization cluster" in w for w in res["warnings"])
    assert any("Formulaic participial tail-drag" in w for w in res["warnings"])


def test_extract_epistemic_skeleton_and_verify_candidate():
    original = (
        "High-certainty randomized trials **show** that periconceptional folate (4 mg/day) "
        "cuts neural tube recurrence by 72% (RR = 0.28) in 1991.[^ch01-mrc-folate] "
        "This protection is a *biological customs shield* that is active early."
    )
    skel = extract_epistemic_skeleton(original)
    assert "[^ch01-mrc-folate]" in skel.footnotes
    assert "**show**" in skel.epistemic_verbs
    assert "72%" in skel.quantitative_tokens
    assert "RR = 0.28" in skel.quantitative_tokens
    assert "*biological customs shield*" in skel.italicized_anchors

    # Candidate missing footnote should fail verification
    bad_candidate = (
        "High-certainty randomized trials **show** that periconceptional folate (4 mg/day) "
        "cuts neural tube recurrence by 72% (RR = 0.28) in 1991. "
        "This *biological customs shield* guards the neural tube early."
    )
    ver_bad = verify_sculpted_candidate(original, bad_candidate)
    assert ver_bad["passed"] is False
    assert "[^ch01-mrc-folate]" in ver_bad["missing_footnotes"]

    # Valid kinetic candidate preserving 100% of skeleton should pass
    good_candidate = (
        "High-certainty trials **show** that daily folate (4 mg/day) "
        "cuts neural tube defects by 72% (RR = 0.28) as proved in 1991.[^ch01-mrc-folate] "
        "This *biological customs shield* locks the neural seam shut."
    )
    ver_good = verify_sculpted_candidate(original, good_candidate)
    assert ver_good["passed"] is True
    assert ver_good["copula_ratio_after"] <= ver_good["copula_ratio_before"]


def test_build_sculptor_prompt_and_chapter_pack():
    sample = "The study **suggests** a correlation of .31 in 2015.[^ch01-test]"
    prompt = build_sculptor_prompt(
        sample,
        section_title="II. Mechanism",
        canonical_metaphor="molecular customs checkpoint",
        reasons=["high copula density (50%)"],
    )
    assert "Frozen Epistemic Skeleton" in prompt
    assert "`[^ch01-test]`" in prompt
    assert "`**suggests**`" in prompt
    assert "`molecular customs checkpoint`" in prompt

    pack = generate_chapter_sculpt_pack("parenthood-atlas", "01-before-the-child-is-born", top_k=2)
    assert pack["chapter_slug"] == "01-before-the-child-is-born.md"
    assert pack["chapter_poetics_score"] >= 85.0


def test_hx_micro_qa_includes_poetics_and_sculpt_button():
    try:
        from fastapi.testclient import TestClient
        from bwe.main import app

        client = TestClient(app)
        resp = client.get("/hx/micro-qa/parenthood-atlas/01-before-the-child-is-born")
        assert resp.status_code == 200
        assert "Poetics Score" in resp.text
        assert "Copula Ratio" in resp.text
        assert "data-sculpt-prompt" in resp.text
    except ImportError:
        pytest.skip("TestClient not installed")
