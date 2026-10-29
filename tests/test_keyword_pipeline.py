"""Integration tests for BWE v0.6.0 keyword telemetry and KDP packaging."""

import sqlite3
from pathlib import Path
import pytest

from bwe import db as bwedb
from bwe.schema import KdpMarketingMetadata
from scripts.marketing_intelligence import (
    compute_opportunity_score,
    pack_kdp_boxes,
    KeywordSignal,
    TIER_SEED,
)


def test_kdp_marketing_metadata_validator_50_bytes():
    # Valid boxes under 50 UTF-8 bytes
    valid_boxes = [
        "baby sleep training safe sleep room sharing",
        "peanut butter allergen introduction solids",
        "tongue tie frenotomy infant latch feeding",
        "toddler tantrum emotional regulation discipline",
        "screen time speech development back and forth",
        "early potty toilet learning physical signs",
        "montessori pretend play executive function",
    ]
    meta = KdpMarketingMetadata(
        primary_subtitle="What the Evidence Shows for the First Three Years",
        backend_keywords=valid_boxes,
    )
    assert len(meta.backend_keywords) == 7

    # Reject boxes with > 50 UTF-8 bytes
    invalid_boxes = valid_boxes.copy()
    invalid_boxes[0] = "this search term box is definitely way too long and exceeds fifty utf8 bytes by far"
    with pytest.raises(ValueError, match="exceed 50 UTF-8 bytes"):
        KdpMarketingMetadata(
            primary_subtitle="What the Evidence Shows for the First Three Years",
            backend_keywords=invalid_boxes,
        )


def test_pack_kdp_boxes():
    signals = [
        KeywordSignal(
            query="when to introduce peanut butter baby",
            monthly_volume=74000,
            yoy_trend_pct=28.5,
            competition_index=0.42,
            target_chapter="04",
            paa_hook="",
            chapter_score=0.85,
            card_score=0.80,
            opportunity_score=15000.0,
        ),
        KeywordSignal(
            query="safe sleep seven room sharing vs own room SIDS",
            monthly_volume=60500,
            yoy_trend_pct=22.0,
            competition_index=0.35,
            target_chapter="04",
            paa_hook="",
            chapter_score=0.90,
            card_score=0.85,
            opportunity_score=12000.0,
        ),
        KeywordSignal(
            query="tongue tie surgery baby necessary frenotomy",
            monthly_volume=45000,
            yoy_trend_pct=48.0,
            competition_index=0.51,
            target_chapter="03",
            paa_hook="",
            chapter_score=0.88,
            card_score=0.82,
            opportunity_score=10000.0,
        ),
        KeywordSignal(
            query="3 day potty training method readiness signs",
            monthly_volume=90500,
            yoy_trend_pct=31.0,
            competition_index=0.46,
            target_chapter="10",
            paa_hook="",
            chapter_score=0.84,
            card_score=0.75,
            opportunity_score=18000.0,
        ),
    ]

    title = "Parenthood: The Atlas"
    subtitle = "What the Evidence Shows for the First Three Years"

    boxes, captured, total = pack_kdp_boxes(
        signals, excluded_text=f"{title} {subtitle}", boxes=7, max_bytes=49
    )
    assert len(boxes) <= 7
    for box in boxes:
        utf8_len = len(box.encode("utf-8"))
        assert utf8_len <= 49, f"Box '{box}' is {utf8_len} bytes (> 49)"

        # Ensure title/subtitle terms are not in the boxes
        words = set(box.split())
        assert "parenthood" not in words
        assert "atlas" not in words
        assert "evidence" not in words


def test_compute_opportunity_score():
    # Base case: volume 10,000, 0% trend, 0 cpc, 0 coverage
    base = compute_opportunity_score(vol=10000, yoy=0.0, cpc_high=0.0, chapter_cov=0.0, card_cov=0.0)
    assert base == 10000.0

    # High trend (+50%) increases score
    trending = compute_opportunity_score(vol=10000, yoy=50.0, cpc_high=0.0, chapter_cov=0.0, card_cov=0.0)
    assert trending == 15000.0

    # Negative trend does not penalize below 1.0 multiplier
    declining = compute_opportunity_score(vol=10000, yoy=-30.0, cpc_high=0.0, chapter_cov=0.0, card_cov=0.0)
    assert declining == 10000.0

    # High commercial intent (CPC $5.00) boosts score
    cpc_boost = compute_opportunity_score(vol=10000, yoy=0.0, cpc_high=5.0, chapter_cov=0.0, card_cov=0.0)
    assert cpc_boost > base

    # High coverage (chapter_cov=1.0, card_cov=1.0) discounts score by factor of 4 (1 / (1 + 2*1 + 1*1))
    covered = compute_opportunity_score(vol=10000, yoy=0.0, cpc_high=0.0, chapter_cov=1.0, card_cov=1.0)
    assert pytest.approx(covered, 0.01) == 2500.0


def test_bwe_db_bm25_coverage_in_memory():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    bwedb.init_db(conn=conn)

    # Populate chapters_fts
    conn.execute(
        "INSERT INTO chapters_fts (series_slug, book_slug, chapter_slug, title, body) VALUES (?, ?, ?, ?, ?)",
        ("series-test", "root", "04-allergens", "Allergen Introduction", "peanut butter introduction in infants reduces allergy risk in randomized trials"),
    )
    conn.execute(
        "INSERT INTO chapters_fts (series_slug, book_slug, chapter_slug, title, body) VALUES (?, ?, ?, ?, ?)",
        ("series-test", "root", "10-potty", "Toilet Training", "potty training readiness signs include physical control and dry diapers"),
    )

    # Populate evidence_cards_fts
    conn.execute(
        "INSERT INTO evidence_cards_fts (series_slug, book_slug, card_slug, title, body) VALUES (?, ?, ?, ?, ?)",
        ("series-test", "root", "card-leap-peanut", "LEAP Trial", "early peanut consumption prevents peanut allergy oral tolerance induction"),
    )

    # Search for peanut allergy query
    cov = bwedb.bm25_coverage(conn, "series-test", ["peanut", "allergen", "introduction"])
    assert cov.chapter_score > 0.5
    assert cov.card_score > 0.4
    assert cov.chapter == "04-allergens"
    assert cov.card == "card-leap-peanut"

    # Search for unrelated query
    cov_unrelated = bwedb.bm25_coverage(conn, "series-test", ["quantum", "teleportation"])
    assert cov_unrelated.chapter_score == 0.0
    assert cov_unrelated.card_score == 0.0


def test_export_amazon_ads_csv(tmp_path):
    from scripts.marketing_intelligence import export_amazon_ads_csv
    signals = [
        KeywordSignal(
            query="when to introduce peanut butter baby",
            monthly_volume=74000,
            yoy_trend_pct=28.5,
            competition_index=0.42,
            target_chapter="04",
            paa_hook="",
            chapter_score=0.85,
            card_score=0.80,
            cpc_low_usd=0.45,
            cpc_high_usd=1.85,
        ),
        KeywordSignal(
            query="safe sleep seven room sharing vs own room SIDS",
            monthly_volume=60500,
            yoy_trend_pct=22.0,
            competition_index=0.35,
            target_chapter="04",
            paa_hook="",
            chapter_score=0.90,
            card_score=0.85,
            cpc_low_usd=0.0,
            cpc_high_usd=0.0,
        ),
    ]
    out_csv = tmp_path / "amazon_ads_test.csv"
    count = export_amazon_ads_csv(signals, "parenthood-atlas", out_csv)
    assert count == 4  # 2 keywords * (EXACT + PHRASE)
    assert out_csv.is_file()

    lines = out_csv.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("Product,Entity,Operation")
    assert "Campaign" in lines[1]
    assert "Ad Group" in lines[2]
    # Check that EXACT and PHRASE are generated
    assert any("EXACT" in line for line in lines[3:])
    assert any("PHRASE" in line for line in lines[3:])


def test_is_domain_relevant():
    from scripts.marketing_intelligence import is_domain_relevant

    # Negative tokens should be rejected immediately regardless of anchors or score
    assert not is_domain_relevant("white noise machine for office", "parenthood-atlas")
    assert not is_domain_relevant("adult sleep apnea machine", "parenthood-atlas")
    assert not is_domain_relevant("gaming headset for toddler", "parenthood-atlas")
    assert not is_domain_relevant("enterprise software memory management", "architectures-of-memory")

    # Domain anchors for parenthood-atlas
    assert is_domain_relevant("when to introduce peanut butter baby", "parenthood-atlas")
    assert is_domain_relevant("why do toddlers hit and bite", "parenthood-atlas")
    assert is_domain_relevant("newborn safe sleep room sharing", "parenthood-atlas")
    assert is_domain_relevant("potty training 3 day method", "parenthood-atlas")

    # Domain anchors for architectures-of-memory
    assert is_domain_relevant("lstm forget gate mechanism", "architectures-of-memory")
    assert is_domain_relevant("transformer multi head attention", "architectures-of-memory")
    assert is_domain_relevant("machine unlearning differential privacy", "architectures-of-memory")

    # Unrelated queries lacking domain anchors should be rejected when BM25 is low
    assert not is_domain_relevant("best vacuum cleaner reviews", "parenthood-atlas", bm25_score=0.1)
    assert not is_domain_relevant("how to bake sourdough bread", "architectures-of-memory", bm25_score=0.0)

    # High BM25 score overrides lack of domain anchors (if no negative tokens)
    assert is_domain_relevant("funes the memorious borges", "architectures-of-memory", bm25_score=0.65)


def test_hardened_box_stopwords():
    from scripts.marketing_intelligence import BOX_STOPWORDS, KDP_STOP_WORDS

    # Ensure alias
    assert BOX_STOPWORDS is KDP_STOP_WORDS

    # Hardened conversational verbs, numbers, and generic nouns
    expected_stopwords = {
        "work", "works", "get", "gets", "own", "day", "three", "seven",
        "study", "method", "signs", "introduce", "book", "books",
    }
    for word in expected_stopwords:
        assert word in BOX_STOPWORDS, f"Expected '{word}' to be in BOX_STOPWORDS"

