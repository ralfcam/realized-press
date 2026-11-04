# tests/test_okf_v03_governance.py
"""
Deterministic test suite for OKF v0.3 Governance, Rule 7f, Rule 7g,
Agent Mirror Parity, CLI Graph Gaps/Stats, and Brief Drawer v0.3 Rendering (ARC-92).
"""
from __future__ import annotations

import re
import sys
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
import pytest
import yaml
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from five_rule_check import check_card
from audit_manuscript import audit_graph_coherence
from bwe.db import get_db, init_db
from bwe.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# =========================================================================
# 1. RULE 7f TESTS (Quantitative Anchors & Typed Semantic Edge Parity)
# =========================================================================

def test_rule_7f_positive_all_143_production_cards():
    """Verify all 143 production OKF v0.3 cards strictly pass Rule 7f."""
    pa_cards = [
        p for p in (REPO_ROOT / "series" / "parenthood-atlas" / "evidence-cards").glob("*.md")
        if not p.name.startswith("_") and p.name != "index.md"
    ]
    aom_cards = [
        p for p in (REPO_ROOT / "series" / "architectures-of-memory").glob("book-*/evidence-cards/*.md")
        if not p.name.startswith("_") and p.name != "index.md"
    ]
    total_cards = pa_cards + aom_cards

    assert len(pa_cards) == 78, f"Expected 78 parenthood-atlas cards, found {len(pa_cards)}"
    assert len(aom_cards) == 65, f"Expected 65 architectures-of-memory cards, found {len(aom_cards)}"
    assert len(total_cards) == 143, f"Expected 143 total cards, found {len(total_cards)}"

    ALLOWED_TIERS = {"formal_proof", "robust_<20%", "partially_confounded_20_50%", "largely_confounded_>50%"}
    ALLOWED_PREFIXES = ("EXTENDS:", "BOUNDS:", "CONTRASTS:", "MITIGATES:", "BRIDGES_LENS:", "CROSS_BOOK_ESCALATES:")

    for card_path in total_cards:
        if card_path.name.startswith("_"):
            continue
        res = check_card(card_path)
        assert res["rule7f_pass"] is True, f"Card {card_path.name} failed Rule 7f: {res['rule7f_notes']}"
        assert res["attenuation_tier"] in ALLOWED_TIERS, f"Card {card_path.name} has invalid tier: {res['attenuation_tier']}"
        assert len(res["quantitative_anchors"]) >= 2, f"Card {card_path.name} has < 2 quantitative anchors"
        for rel in res["relates_to_cards"]:
            assert any(rel.startswith(pfx) for pfx in ALLOWED_PREFIXES), (
                f"Card {card_path.name} has untyped relation: {rel}"
            )


def test_rule_7f_negative_missing_attenuation_tier(tmp_path: Path):
    """Verify check_card flags a card missing or having invalid attenuation_tier."""
    bad_card = tmp_path / "bad-tier-card.md"
    bad_card.write_text(
        """---
type: evidence-card
title: Bad Tier Card
description: Test card missing attenuation tier.
confidence: High
status: stable
tags: [test]
sources:
  - id: test-2024
    resource: https://doi.org/10.1000/182
quantitative_anchors:
  - "Anchor 1"
  - "Anchor 2"
relates_to_cards:
  - "EXTENDS: valid-card"
---
## What We Know
Valid conclusion.
## How Confident We Are
High confidence.
## Evidence and Causal Assessment
Study.
## Effect Size and Persistence
Size.
## Bias, Heterogeneity, and Confounding
Classified as robust (<20%).
## What Remains Uncertain
Uncertainty.
## What This Does Not Mean
Boundaries.
## What Action Is Reasonably Justified
Action.
## Sources
- test-2024
""",
        encoding="utf-8",
    )
    res = check_card(bad_card)
    assert res["rule7f_pass"] is False
    assert any("attenuation_tier invalid or missing" in note for note in res["rule7f_notes"])


def test_rule_7f_negative_insufficient_quantitative_anchors(tmp_path: Path):
    """Verify check_card flags a card with fewer than 2 quantitative anchors."""
    bad_card = tmp_path / "bad-anchors-card.md"
    bad_card.write_text(
        """---
type: evidence-card
title: Bad Anchors Card
description: Test card with only 1 anchor.
confidence: High
status: stable
attenuation_tier: robust_<20%
tags: [test]
sources:
  - id: test-2024
    resource: https://doi.org/10.1000/182
quantitative_anchors:
  - "Only one anchor"
relates_to_cards:
  - "EXTENDS: valid-card"
---
## What We Know
Valid conclusion.
## How Confident We Are
High confidence.
## Evidence and Causal Assessment
Study.
## Effect Size and Persistence
Size.
## Bias, Heterogeneity, and Confounding
Classified as robust (<20%).
## What Remains Uncertain
Uncertainty.
## What This Does Not Mean
Boundaries.
## What Action Is Reasonably Justified
Action.
## Sources
- test-2024
""",
        encoding="utf-8",
    )
    res = check_card(bad_card)
    assert res["rule7f_pass"] is False
    assert any("quantitative_anchors must have >= 2 items" in note for note in res["rule7f_notes"])


def test_rule_7f_negative_untyped_relates_to_cards(tmp_path: Path):
    """Verify check_card flags untyped relates_to_cards entries."""
    bad_card = tmp_path / "untyped-rel-card.md"
    bad_card.write_text(
        """---
type: evidence-card
title: Untyped Rel Card
description: Test card with untyped relates_to_cards slug.
confidence: High
status: stable
attenuation_tier: robust_<20%
tags: [test]
sources:
  - id: test-2024
    resource: https://doi.org/10.1000/182
quantitative_anchors:
  - "Anchor 1"
  - "Anchor 2"
relates_to_cards:
  - "untyped-card-slug-without-prefix"
---
## What We Know
Valid conclusion.
## How Confident We Are
High confidence.
## Evidence and Causal Assessment
Study.
## Effect Size and Persistence
Size.
## Bias, Heterogeneity, and Confounding
Classified as robust (<20%).
## What Remains Uncertain
Uncertainty.
## What This Does Not Mean
Boundaries.
## What Action Is Reasonably Justified
Action.
## Sources
- test-2024
""",
        encoding="utf-8",
    )
    res = check_card(bad_card)
    assert res["rule7f_pass"] is False
    assert any("untyped relates_to_cards entries" in note for note in res["rule7f_notes"])


# =========================================================================
# 2. RULE 7g TESTS (Zero Orphaned Cards & Cross-Edition Parity)
# =========================================================================

def test_rule_7g_positive_zero_orphaned_cards_across_volumes():
    """Verify audit_graph_coherence confirms 0 orphaned cards across all volumes."""
    # Test all 5 AoM books
    for b_slug in [
        "book-01-vanishing-signal",
        "book-02-forget-gate",
        "book-03-weight-of-attention",
        "book-04-context-window",
        "book-05-architecture-of-forgetting",
    ]:
        b_dir = REPO_ROOT / "series" / "architectures-of-memory" / b_slug
        lines, violations, is_ok = audit_graph_coherence(REPO_ROOT, b_dir)
        rule7g_violations = [v for v in violations if "Rule 7g" in v or "Orphaned card" in v]
        assert len(rule7g_violations) == 0, f"Rule 7g violation in {b_slug}: {rule7g_violations}"
        assert is_ok is True

    # Test PA English
    pa_dir = REPO_ROOT / "series" / "parenthood-atlas"
    lines, violations, is_ok = audit_graph_coherence(REPO_ROOT, pa_dir)
    rule7g_violations = [v for v in violations if "Rule 7g" in v or "Orphaned card" in v]
    assert len(rule7g_violations) == 0, f"Rule 7g violation in parenthood-atlas: {rule7g_violations}"
    assert is_ok is True


def test_rule_7g_positive_cross_edition_citation_parity():
    """Verify 100% citation parity between PA English and Spanish editions."""
    es_dir = REPO_ROOT / "series" / "parenthood-atlas" / "i18n" / "es"
    lines, violations, is_ok = audit_graph_coherence(REPO_ROOT, es_dir, lang="es")
    parity_violations = [v for v in violations if "Cross-edition citation mismatch" in v or "Orphaned card" in v]
    assert len(parity_violations) == 0, f"Parity violations: {parity_violations}"
    assert is_ok is True


def test_rule_7g_negative_orphaned_card_flagged():
    """Verify Rule 7g flags an unreferenced card as an orphan."""
    conn = get_db()
    row = conn.execute("SELECT node_id FROM okf_nodes WHERE series_slug='parenthood-atlas' AND node_type='card' LIMIT 1").fetchone()
    card_id = row["node_id"]

    # Backup the existing edges for this card
    cites = conn.execute(
        "SELECT * FROM okf_edges WHERE series_slug='parenthood-atlas' AND (target_id = ? OR (source_id = ? AND edge_type='CITED_IN_MOVEMENT'))",
        (card_id, card_id),
    ).fetchall()
    cites_data = [dict(r) for r in cites]

    try:
        conn.execute("DELETE FROM okf_edges WHERE series_slug='parenthood-atlas' AND target_id = ?", (card_id,))
        conn.execute("DELETE FROM okf_edges WHERE series_slug='parenthood-atlas' AND source_id = ? AND edge_type='CITED_IN_MOVEMENT'", (card_id,))
        conn.commit()

        lines, violations, is_ok = audit_graph_coherence(REPO_ROOT, REPO_ROOT / "series" / "parenthood-atlas")
        orphan_hits = [v for v in violations if "Orphaned card" in v and card_id.split(":")[-1] in v]
        assert len(orphan_hits) > 0, "Expected Rule 7g to flag unreferenced card as orphan"
        assert is_ok is False
    finally:
        for r in cites_data:
            conn.execute(
                """INSERT INTO okf_edges (series_slug, source_id, target_id, edge_type, weight, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (r["series_slug"], r["source_id"], r["target_id"], r["edge_type"], r["weight"], r["metadata_json"]),
            )
        conn.commit()


def test_rule_7g_negative_citation_parity_mismatch_flagged():
    """Verify Rule 7g flags cross-edition citation set divergence between EN and ES."""
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO okf_edges (series_slug, source_id, target_id, edge_type, weight, metadata_json)
               VALUES ('parenthood-atlas/i18n/es', 'ch:parenthood-atlas:01-before-the-child-is-born', 'card:parenthood-atlas:bogus-synthetic-card-999', 'CITES_CARD', 1.0, '{}')"""
        )
        conn.commit()
        lines, violations, is_ok = audit_graph_coherence(REPO_ROOT, REPO_ROOT / "series" / "parenthood-atlas" / "i18n" / "es", lang="es")
        mismatch_hits = [v for v in violations if "Cross-edition citation mismatch" in v and "bogus-synthetic-card-999" in v]
        assert len(mismatch_hits) > 0, "Expected cross-edition citation mismatch to be flagged"
        assert is_ok is False
    finally:
        conn.execute("DELETE FROM okf_edges WHERE series_slug='parenthood-atlas/i18n/es' AND target_id='card:parenthood-atlas:bogus-synthetic-card-999'")
        conn.commit()


# =========================================================================
# 3. CLI GRAPH --STATS & --GAPS TESTS
# =========================================================================

def test_cli_graph_stats_and_gaps_execution():
    """Verify bwe.cli graph --stats and --gaps commands execute cleanly."""
    # 1. Stats for architectures-of-memory
    p1 = subprocess.run(
        [sys.executable, "-m", "bwe.cli", "graph", "--series", "architectures-of-memory", "--stats"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert p1.returncode == 0, f"CLI stats failed: {p1.stderr}"
    assert "orphaned_cards: 0" in p1.stdout
    assert "Evidence Cards:     65" in p1.stdout

    # 2. Stats for parenthood-atlas
    p2 = subprocess.run(
        [sys.executable, "-m", "bwe.cli", "graph", "--series", "parenthood-atlas", "--stats"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert p2.returncode == 0, f"CLI stats failed: {p2.stderr}"
    assert "orphaned_cards: 0" in p2.stdout
    assert "Evidence Cards:     78" in p2.stdout

    # 3. Gaps for parenthood-atlas
    p3 = subprocess.run(
        [sys.executable, "-m", "bwe.cli", "graph", "--series", "parenthood-atlas", "--gaps"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert p3.returncode == 0, f"CLI gaps failed: {p3.stderr}"
    assert "[GRAPH DEMAND GAPS]" in p3.stdout
    assert "Coverage Weight:" in p3.stdout


# =========================================================================
# 4. AGENT RULE & SKILL MIRROR PARITY TEST
# =========================================================================

def test_agent_rule_and_skill_mirror_parity():
    """Verify 100% parity between .agents/, .cursor/, and plugins/realized-bwe/."""
    # 1. Rules parity
    agent_rules = sorted((REPO_ROOT / ".agents" / "rules").glob("*.md"))
    assert len(agent_rules) >= 10, f"Expected at least 10 agent rules, found {len(agent_rules)}"

    for a_rule in agent_rules:
        c_rule = REPO_ROOT / ".cursor" / "rules" / (a_rule.stem + ".mdc")
        assert c_rule.exists(), f"Missing cursor rule corresponding to {a_rule.name}"

        a_text = a_rule.read_text(encoding="utf-8")
        c_text = c_rule.read_text(encoding="utf-8")

        # Strip optional frontmatter for body comparison
        a_body = a_text
        if a_text.startswith("---"):
            parts = a_text.split("---", 2)
            if len(parts) >= 3:
                a_body = parts[2].strip()

        c_body = c_text
        if c_text.startswith("---"):
            parts = c_text.split("---", 2)
            if len(parts) >= 3:
                c_body = parts[2].strip()

        assert a_body.strip() == c_body.strip(), (
            f"Rule body mismatch between {a_rule.name} and {c_rule.name}"
        )

    # 2. Skills parity
    skills = [
        "audiobook-tts",
        "chapter-draft",
        "evidence-card-pass",
        "fact-check-pass",
        "manuscript-audit",
        "refinement-pass",
        "research-loop",
    ]
    for s in skills:
        s_agent = (REPO_ROOT / ".agents" / "skills" / s / "SKILL.md").read_text(encoding="utf-8")
        s_cursor = (REPO_ROOT / ".cursor" / "skills" / s / "SKILL.md").read_text(encoding="utf-8")
        s_plugin = (REPO_ROOT / "plugins" / "realized-bwe" / "skills" / s / "SKILL.md").read_text(encoding="utf-8")

        assert s_agent == s_cursor, f"Skill mismatch between .agents and .cursor for {s}"
        assert s_agent == s_plugin, f"Skill mismatch between .agents and plugins/realized-bwe for {s}"


# =========================================================================
# 5. BRIEF DRAWER OKF v0.3 MARKUP & COMPLIANCE TEST
# =========================================================================

def test_brief_drawer_okf_v03_markup_and_compliance(client: TestClient):
    """Verify /hx/brief/ returns accessible OKF v0.3 drawer with anchors, tier and neighbor links."""
    endpoints = [
        "/hx/brief/parenthood-atlas/early-allergen-introduction-blw",
        "/hx/brief/architectures-of-memory/hochreiter-1991-vanishing-gradient",
    ]

    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Expected 200 for {ep}, got {res.status_code}"
        html = res.text

        # 1. OKF v0.3 marker
        assert "OKF v0.3" in html, f"Missing 'OKF v0.3' badge in {ep}"

        # 2. Attenuation tier badge
        assert "Tier: " in html, f"Missing attenuation tier badge in {ep}"

        # 3. Quantitative anchors section
        assert "Quantitative Anchors" in html, f"Missing 'Quantitative Anchors' in {ep}"

        # 4. Epistemic neighbor cards
        assert "Epistemic Neighbor Cards" in html, f"Missing 'Epistemic Neighbor Cards' in {ep}"
        assert 'hx-get="/hx/brief/' in html, f"Missing clickable HTMX neighbor buttons in {ep}"

        # 5. Accessibility & Contrast check
        soup = BeautifulSoup(html, "html.parser")
        dialog = soup.find(attrs={"role": "dialog"})
        assert dialog is not None, "Missing role='dialog'"
        assert dialog.get("aria-modal") == "true"

        # Check interactive buttons have min 44px
        buttons = soup.find_all("button")
        assert len(buttons) >= 2, "Drawer should have at least close/dismiss and neighbor buttons"
        for btn in buttons:
            cls = " ".join(btn.get("class", []))
            assert "min-h-[44px]" in cls or "min-w-[44px]" in cls, f"Button missing 44px dimensions: {btn}"

        # Verify no low contrast classes (stone-500/600/700) or red alert tokens
        assert not re.search(r"\btext-stone-[567]00\b", html), "Found low contrast text-stone class"
        assert not re.search(r"\b(?:text|bg|border)-red-[456]00\b", html), "Found non-compliant red token"


# =========================================================================
# 6. EPISTEMIC DEMAND CARD ROUTING TESTS (ARC-93)
# =========================================================================

def test_epistemic_demand_card_routing():
    """Verify term-fraction gating and co-citation weighting prevent false-positive ANSWERS_DEMAND edges."""
    from bwe.db import get_db, bm25_coverage

    conn = get_db()

    # 1. Daycare / Nanny routing
    cov_nanny = bm25_coverage(conn, "parenthood-atlas", ["daycare", "or", "nanny"])
    assert cov_nanny.card != "severe-institutional-deprivation", "Routine childcare must not route to severe-institutional-deprivation"
    assert cov_nanny.card == "early-childcare-quality", f"Expected early-childcare-quality, got {cov_nanny.card}"
    assert cov_nanny.card_score > 0.50

    # 2. Daycare cortisol comparison
    cov_cortisol = bm25_coverage(conn, "parenthood-atlas", ["daycare", "vs", "stay", "at", "home", "mom", "cortisol", "study"])
    assert cov_cortisol.card == "early-childcare-quality", f"Expected early-childcare-quality, got {cov_cortisol.card}"
    assert cov_cortisol.card_score > 0.50

    # 3. 18-month vocabulary query cluster
    for q_tokens in [
        ["how", "many", "words", "should", "18", "month", "say"],
        ["how", "many", "words", "18", "months"],
        ["how", "many", "words", "does", "18", "month", "old", "say"],
    ]:
        cov_words = bm25_coverage(conn, "parenthood-atlas", q_tokens)
        assert cov_words.chapter == "07-the-birth-of-language", f"Expected Ch 07, got {cov_words.chapter}"
        assert cov_words.card == "conversational-turns-language", f"Expected conversational-turns-language, got {cov_words.card}"
        assert cov_words.card_score > 0.50

    # 4. Newborn phototherapy routing (ARC-94)
    from scripts.marketing_intelligence import is_domain_relevant
    assert is_domain_relevant("newborn photo therapy", "parenthood-atlas") is True

    cov_photo = bm25_coverage(conn, "parenthood-atlas", ["newborn", "photo", "therapy"], repo_root=REPO_ROOT)
    assert cov_photo.card != "plagiocephaly-flat-head-helmet-rct", "Newborn phototherapy must not match helmet therapy"
    assert cov_photo.card == "neonatal-cardiopulmonary-transition", f"Expected neonatal-cardiopulmonary-transition, got {cov_photo.card}"
    assert cov_photo.card_score >= 0.45
    assert cov_photo.combined >= 0.45

    # 5. Cross-lingual demand routing (parenthood-atlas/i18n/es -> English OKF cards)
    es_queries = [
        ("metodo ferber sueno bebe llanto", "infant-sleep-training"),
        ("dejar el panal control de esfinteres senales", "toilet-learning-readiness"),
        ("personalidad fija a los tres anos neurodesarrollo", "temperament-reactivity-not-destiny"),
        ("rabietas berrinches como calmar a un nino de dos anos", "temperament-reactivity-not-destiny"),
        ("guarderia o quedarse en casa apego cortisol", "early-childcare-quality"),
    ]
    for q_text, expected_card in es_queries:
        cov_es = bm25_coverage(conn, "parenthood-atlas/i18n/es", q_text.split(), repo_root=REPO_ROOT)
        assert cov_es.card == expected_card, f"Query '{q_text}' expected card {expected_card}, got {cov_es.card}"
        assert cov_es.card_score >= 0.45, f"Query '{q_text}' card_score {cov_es.card_score:.4f} < 0.45"
        assert cov_es.combined >= 0.45
