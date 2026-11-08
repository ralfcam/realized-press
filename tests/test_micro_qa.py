"""tests/test_micro_qa.py: Unit and regression test suite for BWE v1.3.0 Sentence & Paragraph Micro-QA Gates (ARC-101).

Tests:
1. Sentence tokenization, abbreviations, decimal protection, and duration estimation.
2. Rule 8a: Sentence breath ceiling (35w EN / 38w ES), semicolon bloat (>2), oral breath strain (>30w no punctuation).
3. Rule 8b: Paragraph visual geometry (135w, 6s) and local rolling readability outliers.
4. Rule 8c: Uncited empirical claim markers vs footnote parity.
5. Rule 8d: Starter monotony, cadence variance, and non-defeatist movement closings.
6. HTML `<aside>` callout block isolation.
7. FastAPI endpoint `/hx/micro-qa/{series_slug}/{chapter_slug}` response conformance.
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

from audit_manuscript import (
    tokenize_sentences,
    audit_micro_qa,
    EMPIRICAL_STUDY_PATTERNS,
    EMPIRICAL_EXCLUSIONS_RE,
    DEFEATIST_PATTERNS,
)


# -------------------------------------------------------------------------
# 1. Sentence Tokenizer Tests
# -------------------------------------------------------------------------


def test_tokenize_sentences_basic():
    text = "This is sentence one. Here is sentence two! Is this sentence three?"
    sents = tokenize_sentences(text, language="en")
    assert len(sents) == 3
    assert sents[0]["words"] == 4
    assert sents[0]["starts_with"] == "this"
    assert sents[1]["words"] == 4
    assert sents[2]["words"] == 4


def test_tokenize_sentences_abbreviations_and_decimals():
    text = (
        "In 1991, Dr. Smith et al. evaluated No. 4 with a risk ratio of 0.28. "
        "The follow-up was successful."
    )
    sents = tokenize_sentences(text, language="en")
    assert len(sents) == 2
    assert "Dr. Smith" in sents[0]["text"]
    assert "0.28" in sents[0]["text"]
    assert sents[1]["text"].startswith("The follow-up")


def test_tokenize_sentences_spanish_accents_and_decimals():
    text = (
        "El ensayo clínico evaluó a 1.817 niños con un RR de 1,24. "
        "La protección biológica resultó evidente."
    )
    sents = tokenize_sentences(text, language="es")
    assert len(sents) == 2
    assert "1,24" in sents[0]["text"]
    assert sents[1]["starts_with"] == "la"


def test_tokenize_sentences_metrics():
    text = "This sentence has one semicolon; and one em-dash—making two clauses."
    sents = tokenize_sentences(text, language="en")
    assert len(sents) == 1
    assert sents[0]["semicolons"] == 1
    assert sents[0]["dashes"] >= 1
    assert sents[0]["has_internal_punct"] is True
    assert sents[0]["spoken_duration_s"] > 0


# -------------------------------------------------------------------------
# 2. Rule 8a: Sentence Breath & Clause Outlier Cap
# -------------------------------------------------------------------------


def test_rule_8a_sentence_breath_ceiling_english():
    # 36 words > 35 words target
    long_sent = " ".join(["word"] * 36) + "."
    body = f"## I. Test Movement\n\n{long_sent}\n"
    hard_errors, warnings, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Sentence breath ceiling exceeded: 36w" in e for e in hard_errors)
    assert metrics["over_breath_sents"] == 1

    # 34 words <= 35 words target
    ok_sent = " ".join(["word"] * 34) + "."
    body_ok = f"## I. Test Movement\n\n{ok_sent}\n"
    hard_errors_ok, _, _ = audit_micro_qa(body_ok, language="en", chapter_slug="ch01")
    assert not any("Sentence breath ceiling exceeded" in e for e in hard_errors_ok)


def test_rule_8a_sentence_breath_ceiling_spanish():
    # 39 words > 38 words target for ES
    long_sent = " ".join(["palabra"] * 39) + "."
    body = f"## I. Movimiento\n\n{long_sent}\n"
    hard_errors, warnings, metrics = audit_micro_qa(body, language="es", chapter_slug="ch01")
    assert any("Sentence breath ceiling exceeded: 39w" in e for e in hard_errors)

    # 37 words <= 38 words target for ES
    ok_sent = " ".join(["palabra"] * 37) + "."
    body_ok = f"## I. Movimiento\n\n{ok_sent}\n"
    hard_errors_ok, _, _ = audit_micro_qa(body_ok, language="es", chapter_slug="ch01")
    assert not any("Sentence breath ceiling exceeded" in e for e in hard_errors_ok)


def test_rule_8a_semicolon_bloat():
    bloated = "Clause one; clause two; clause three; clause four."
    body = f"## I. Test\n\n{bloated}\n"
    hard_errors, _, _ = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Clause bloat (>2 semicolons or >2 em-dash parentheticals in single sentence)" in e for e in hard_errors)


def test_rule_8a_oral_breath_strain():
    # 32 words with NO comma, semicolon, colon, or dash
    strain = "Look back one more time at the nurse pressing five drops of blood onto a paper card and the father pausing a tablet video on the couch to catch her glance."
    body = f"## I. Test\n\n{strain}\n"
    hard_errors, _, _ = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Oral breath strain" in e for e in hard_errors)

    # Adding a comma relieves breath strain
    relieved = "Look back one more time at the nurse pressing five drops of blood onto a paper card, and the father pausing a tablet video on the couch to catch her glance."
    body_relieved = f"## I. Test\n\n{relieved}\n"
    hard_errors_relieved, _, _ = audit_micro_qa(body_relieved, language="en", chapter_slug="ch01")
    assert not any("Oral breath strain" in e for e in hard_errors_relieved)


# -------------------------------------------------------------------------
# 3. Rule 8b: Paragraph Visual Geometry & Rolling Readability
# -------------------------------------------------------------------------


def test_rule_8b_wall_of_text_warning():
    # > 135 words in single paragraph
    long_para = " ".join(["word"] * 140) + "."
    body = f"## I. Test\n\n{long_para}\n"
    _, warnings, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Visual geometry wall-of-text: 140 words" in w for w in warnings)
    assert metrics["wall_of_text_paras"] == 1


def test_rule_8b_paragraph_density_warning():
    # > 6 sentences in single paragraph
    para_7_sents = " ".join([f"Sentence number {i} is short." for i in range(1, 8)])
    body = f"## I. Test\n\n{para_7_sents}\n"
    _, warnings, _ = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Visual paragraph density: 7 sentences" in w for w in warnings)


def test_rule_8b_extreme_academic_density_hard_error():
    # Extremely dense academic vocabulary yielding FK Grade > 16.0 across >=3 sentences
    dense_text = (
        "The epistemological recontextualization of multidimensional phenomenological hermeneutics "
        "substantiates the hyperparameterized operationalization of counterfactual inferential architectures. "
        "Such macroscopic computational formalisms necessitate deterministic ontological presuppositions "
        "regarding the non-isomorphic convergence of stochastic gradient backpropagation. "
        "Consequently, the dialectical synthesis remains fundamentally unresolvable within empirical paradigms."
    )
    body = f"## I. Test\n\n{dense_text}\n"
    hard_errors, _, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Extreme local academic density outlier: FK Grade" in e for e in hard_errors)
    assert metrics["density_paras"] == 1


# -------------------------------------------------------------------------
# 4. Rule 8c: Uncited Empirical Claim & Quantitative Anchor Check
# -------------------------------------------------------------------------


def test_rule_8c_uncited_empirical_claim_marker():
    # Body paragraph mentions "In a randomized controlled trial" without footnote
    uncited = "In a randomized controlled trial, children showed remarkable gains in vocabulary when exposed to interactive dialogic reading."
    body = f"## I. Test\n\n{uncited}\n"
    hard_errors, _, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Uncited empirical claim marker" in e for e in hard_errors)
    assert metrics["empirical_errors"] == 1


def test_rule_8c_cited_empirical_claim_passes():
    # Body paragraph mentions empirical study WITH footnote anchor
    cited = "In a randomized controlled trial, children showed remarkable gains in vocabulary when exposed to interactive dialogic reading.[^ch01-reading-rct]"
    body = f"## I. Test\n\n{cited}\n"
    hard_errors, _, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert not any("Uncited empirical claim marker" in e for e in hard_errors)
    assert metrics["empirical_errors"] == 0


def test_rule_8c_empirical_exclusion():
    # Metaphorical phrase "like a clinical trial" should NOT trigger uncited empirical error
    metaphor = "Operating an enterprise like a clinical trial obscures the organic relationship between teams."
    body = f"## I. Test\n\n{metaphor}\n"
    hard_errors, _, _ = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert not any("Uncited empirical claim marker" in e for e in hard_errors)


# -------------------------------------------------------------------------
# 5. Rule 8d: Cadence, Starter Monotony & Defeatist Closings
# -------------------------------------------------------------------------


def test_rule_8d_starter_monotony():
    para = "The child ran to the door. The child looked for the handle. The child asked for assistance."
    body = f"## I. Test\n\n{para}\n"
    _, warnings, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Sentence starter monotony" in w for w in warnings)
    assert metrics["cadence_warnings"] >= 1


def test_rule_8d_low_cadence_variance():
    # 4 sentences with almost identical length (10 words each -> sigma = 0.0)
    p1 = "This is a sentence that has exactly ten little words."
    p2 = "Here is a sentence that has exactly ten little words."
    p3 = "That is a sentence that has exactly ten little words."
    p4 = "Each is a sentence that has exactly ten little words."
    para = f"{p1} {p2} {p3} {p4}"
    body = f"## I. Test\n\n{para}\n"
    _, warnings, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Low sentence cadence variance" in w for w in warnings)


def test_rule_8d_defeatist_movement_closing():
    # Movement ends with defeatist disclaimer without 3-tier resolution
    body = (
        "## I. First Movement\n\n"
        "Early research was ambitious.\n\n"
        "However, this messy observational data completely uninformative and leaves us with nothing."
    )
    hard_errors, _, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Defeatist movement closing terminates on negative disclaimer" in e for e in hard_errors)
    assert metrics["defeatist_closings"] == 1


# -------------------------------------------------------------------------
# 6. Callout Aside Block Stripping
# -------------------------------------------------------------------------


def test_aside_callouts_stripped_from_body_audit():
    # An <aside> block containing bullet points or takeaways should not trigger body density errors
    body = (
        "## I. First Movement\n\n"
        "This is an exemplary narrative paragraph adhering to all bestselling principles.\n\n"
        '<aside class="chapter-takeaway">\n'
        "### Takeaways\n\n"
        "- **The Technical Signal:** Highly specialized mathematical proof with dense terms.\n"
        "- **The Organizational Fallacy:** Deep institutional analysis.\n"
        "</aside>\n"
    )
    hard_errors, warnings, metrics = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert not hard_errors


# -------------------------------------------------------------------------
# 7. FastAPI Endpoint Diagnostics Conformance (/hx/micro-qa/...)
# -------------------------------------------------------------------------


def test_rule_8a_em_dash_bloat():
    # Sentence with >4 em-dashes (>2 parenthetical pairs) should be flagged in hard_errors
    dash_sent = "The fetus—while growing—adapts to cortisol—even when muted—and calibrates—for survival—before birth."
    body = f"## I. Test\n\n{dash_sent}\n"
    hard_errors, _, _ = audit_micro_qa(body, language="en", chapter_slug="ch01")
    assert any("Clause bloat (>2 semicolons or >2 em-dash parentheticals in single sentence)" in e for e in hard_errors)


def test_rule_8c_card_dict_anchor_mismatch_warning():
    # Cited paragraph with N = 9,999 not matching card_dict quantitative_anchors
    cited = "In a randomized controlled trial of N = 9,999 infants, outcomes shifted.[^ch01-mrc]"
    body = f"## I. Test\n\n{cited}\n"
    card_dict = {
        "ch01-mrc": {
            "quantitative_anchors": ["N = 1,817 high-risk pregnancies", "RR = 0.28"]
        }
    }
    _, warnings, _ = audit_micro_qa(body, language="en", chapter_slug="ch01", card_dict=card_dict)
    assert any("Quantitative anchor token" in w for w in warnings)


def test_hx_micro_qa_endpoint():
    try:
        from fastapi.testclient import TestClient
        from bwe.main import app

        client = TestClient(app)
        resp = client.get("/hx/micro-qa/parenthood-atlas/01-before-the-child-is-born")
        assert resp.status_code == 200
        assert "Micro-QA Diagnostics (Rules 8a–8d)" in resp.text
        assert "01-before-the-child-is-born" in resp.text
        assert "Over-Breath Sents" in resp.text
        assert "Paragraph Diagnostics" in resp.text
    except ImportError:
        pytest.skip("TestClient or dependencies not installed")
