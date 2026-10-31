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
    assert not is_domain_relevant("sleep trainer near me", "parenthood-atlas")
    assert not is_domain_relevant("ferber method reddit", "parenthood-atlas")
    assert not is_domain_relevant("sleep tr", "parenthood-atlas")
    assert not is_domain_relevant("vtech sleep trainer", "parenthood-atlas")

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

    # Hardened conversational verbs, numbers, age qualifiers, and generic nouns
    expected_stopwords = {
        "work", "works", "get", "gets", "own", "day", "three", "seven",
        "study", "method", "signs", "introduce", "book", "books",
        "old", "new", "born", "month", "months", "week", "weeks",
        "year", "years", "time", "test",
    }
    for word in expected_stopwords:
        assert word in BOX_STOPWORDS, f"Expected '{word}' to be in BOX_STOPWORDS"


def test_bm25_subtitle_and_ferber_sleep_coverage():
    from scripts.marketing_intelligence import _extract_core_tokens
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    bwedb.init_db(Path("."), conn=conn)

    # Verify "ferber method" and "sleep training baby" link to Chapter 4 and infant-sleep-training above coverage thresholds
    cov_ferber = bwedb.bm25_coverage(conn, "parenthood-atlas", _extract_core_tokens("ferber method"))
    assert cov_ferber.chapter == "04-regulatory-relationship"
    assert cov_ferber.card == "infant-sleep-training"
    assert cov_ferber.chapter_score >= 0.50
    assert cov_ferber.card_score >= 0.40

    cov_sleep = bwedb.bm25_coverage(conn, "parenthood-atlas", _extract_core_tokens("sleep training baby"))
    assert cov_sleep.chapter == "04-regulatory-relationship"
    assert cov_sleep.card == "infant-sleep-training"
    assert cov_sleep.chapter_score >= 0.50
    assert cov_sleep.card_score >= 0.40

    # Verify Chapter 14 links to infant-sleep-training for "ferber method guide"
    cov_ch14 = bwedb.bm25_coverage(conn, "parenthood-atlas", _extract_core_tokens("ferber method guide"))
    assert cov_ch14.chapter == "14-what-actually-works"
    assert cov_ch14.card == "infant-sleep-training"
    assert cov_ch14.chapter_score >= 0.50
    assert cov_ch14.card_score >= 0.40


def test_i18n_fts5_partitioning_and_stemming():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    bwedb.init_db(Path("."), conn=conn)

    # 1. Verify partitioned slugs: exactly 15 English chapters and 15 Spanish chapters
    en_rows = conn.execute("SELECT COUNT(*) AS c FROM chapters_fts WHERE series_slug = 'parenthood-atlas'").fetchone()
    es_rows = conn.execute("SELECT COUNT(*) AS c FROM chapters_fts WHERE series_slug = 'parenthood-atlas/i18n/es'").fetchone()
    assert en_rows["c"] == 15
    assert es_rows["c"] == 15

    # 2. Verify diacritic-folding & Porter stemming in Spanish FTS5
    # Query without accents ("sueno bebe") matches accented chapter prose ("sueño", "bebé")
    cov = bwedb.bm25_coverage(conn, "parenthood-atlas/i18n/es", ["sueno", "bebe", "llanto"])
    assert cov.chapter == "04-regulatory-relationship"
    assert cov.chapter_score >= 0.50


def test_cross_lingual_card_lookup_via_lexicon():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    bwedb.init_db(Path("."), conn=conn)

    # In i18n/es, there are no local evidence cards.
    # Searching for Spanish terms "sueno bebe ferber" maps via style/lexicon.yaml to English card "infant-sleep-training"
    cov = bwedb.bm25_coverage(conn, "parenthood-atlas/i18n/es", ["sueno", "bebe", "ferber"])
    assert cov.chapter == "04-regulatory-relationship"
    assert cov.card == "infant-sleep-training"
    assert cov.card_score >= 0.40
    assert cov.combined >= 0.70


def test_canonicalize_query_cluster_deduplication():
    from scripts.marketing_intelligence import (
        query_cluster_signature,
        canonicalize_query_cluster,
    )

    # 1. Number words vs numerals produce identical cluster signatures
    sig_digit = query_cluster_signature("sleep training 4 month old")
    sig_word = query_cluster_signature("sleep training four month old")
    assert sig_digit == sig_word

    # 2. Method and stop words produce identical signatures
    sig_ferber1 = query_cluster_signature("ferber sleep training")
    sig_ferber2 = query_cluster_signature("ferber method sleep training")
    assert sig_ferber1 == sig_ferber2

    # 3. Canonical representative prefers digits and highest volume
    cluster = [
        ("sleep training four month old", 8100, 0.95, 0.33),
        ("sleep training 4 month old", 8100, 0.95, 0.33),
    ]
    canonical, variants = canonicalize_query_cluster(cluster)
    assert canonical == "sleep training 4 month old"
    assert "sleep training four month old" in variants


def test_kdp_packing_intact_collocations_and_multilingual():
    from scripts.marketing_intelligence import pack_kdp_boxes, KeywordSignal

    # Test English packing preserves 2-word & 3-word intact collocations
    signals = [
        KeywordSignal(
            query="ferber method sleep training baby safe sleep",
            monthly_volume=40500,
            yoy_trend_pct=12.0,
            competition_index=0.25,
            target_chapter="04",
            paa_hook="",
            chapter_score=0.90,
            card_score=0.85,
        ),
        KeywordSignal(
            query="peanut butter allergen introduction baby led weaning",
            monthly_volume=74000,
            yoy_trend_pct=28.0,
            competition_index=0.42,
            target_chapter="04",
            paa_hook="",
            chapter_score=0.88,
            card_score=0.82,
        ),
    ]

    boxes, captured, total = pack_kdp_boxes(signals, excluded_text="Parenthood The Atlas", lang="en")
    assert len(boxes) <= 7
    for b in boxes:
        assert len(b.encode("utf-8")) <= 49

    # Check intact collocations are preserved in box
    all_text = " ".join(boxes)
    assert ("ferber method" in all_text) or ("sleep training" in all_text)

    # Test Spanish stop words are stripped
    signals_es = [
        KeywordSignal(
            query="introduccion de cacahuate y alergias en la alimentacion complementaria",
            monthly_volume=27100,
            yoy_trend_pct=28.0,
            competition_index=0.30,
            target_chapter="04",
            paa_hook="",
            chapter_score=0.85,
            card_score=0.80,
        ),
    ]
    boxes_es, _, _ = pack_kdp_boxes(signals_es, excluded_text="El atlas de la crianza", lang="es")
    for b in boxes_es:
        assert len(b.encode("utf-8")) <= 49
        words = b.split()
        assert "de" not in words
        assert "la" not in words
        assert "en" not in words
        assert "y" not in words


def test_audit_quick_finder_coverage():
    from scripts.marketing_intelligence import audit_quick_finder_coverage, KeywordSignal

    signals = [
        KeywordSignal(
            query="when to introduce peanut butter baby",
            monthly_volume=74000,
            yoy_trend_pct=28.5,
            competition_index=0.42,
            target_chapter="04",
            paa_hook="",
            chapter_score=0.95,
            card_score=0.90,
        ),
    ]

    report = audit_quick_finder_coverage(Path("series/parenthood-atlas"), signals)
    assert "Front-Matter 2:00 AM Quick-Finder Coverage Audit" in report
    assert "MAPPED" in report


def test_arc79_negative_tokens():
    from scripts.marketing_intelligence import is_domain_relevant

    # ARC-79: Block nursing-student homework, academic slide presentations & forum/brand noise
    assert not is_domain_relevant("phototherapy neonatal jaundice nursing ppt", "parenthood-atlas")
    assert not is_domain_relevant("infant sleep training guidelines pdf download", "parenthood-atlas")
    assert not is_domain_relevant("define neonatal jaundice pathophysiology", "parenthood-atlas")
    assert not is_domain_relevant("definition of plagiocephaly in pediatrics", "parenthood-atlas")
    assert not is_domain_relevant("cranial helmet indication for infants", "parenthood-atlas")
    assert not is_domain_relevant("phototherapy indications in newborn care", "parenthood-atlas")
    assert not is_domain_relevant("lil mixins peanut powder baby", "parenthood-atlas")
    assert not is_domain_relevant("baby sleep regression mumsnet", "parenthood-atlas")
    assert not is_domain_relevant("baginal seeding newborn c section", "parenthood-atlas")


def test_arc79_chapter_balanced_kdp_packing():
    from scripts.marketing_intelligence import pack_kdp_boxes, KeywordSignal

    # Construct signals where Ch 04 has huge volume and multiple phrases,
    # but Ch 01, Ch 06, and Ch 07 also have distinct keywords
    signals = [
        # Ch 04 (Sleep): 4 phrases
        KeywordSignal(query="baby sleep training methods", monthly_volume=90000, yoy_trend_pct=10.0,
                      competition_index=0.5, target_chapter="04", paa_hook="", chapter_score=0.95, card_score=0.9, matched_chapter="04-sleep"),
        KeywordSignal(query="infant bedtime routine solutions", monthly_volume=80000, yoy_trend_pct=10.0,
                      competition_index=0.5, target_chapter="04", paa_hook="", chapter_score=0.95, card_score=0.9, matched_chapter="04-sleep"),
        KeywordSignal(query="graduated extinction crying nights", monthly_volume=70000, yoy_trend_pct=10.0,
                      competition_index=0.5, target_chapter="04", paa_hook="", chapter_score=0.95, card_score=0.9, matched_chapter="04-sleep"),
        KeywordSignal(query="infant night awakenings rhythm", monthly_volume=60000, yoy_trend_pct=10.0,
                      competition_index=0.5, target_chapter="04", paa_hook="", chapter_score=0.95, card_score=0.9, matched_chapter="04-sleep"),

        # Ch 01 (Preconception/Folate)
        KeywordSignal(query="prenatal folate nutrition vitamins", monthly_volume=25000, yoy_trend_pct=15.0,
                      competition_index=0.4, target_chapter="01", paa_hook="", chapter_score=0.90, card_score=0.85, matched_chapter="01-preconception"),

        # Ch 06 (Motor / Plagiocephaly)
        KeywordSignal(query="positional plagiocephaly cranial shape", monthly_volume=20000, yoy_trend_pct=12.0,
                      competition_index=0.3, target_chapter="06", paa_hook="", chapter_score=0.90, card_score=0.85, matched_chapter="06-motor"),

        # Ch 07 (Language / 18-month speech)
        KeywordSignal(query="toddler speech milestone vocabulary", monthly_volume=22000, yoy_trend_pct=14.0,
                      competition_index=0.3, target_chapter="07", paa_hook="", chapter_score=0.90, card_score=0.85, matched_chapter="07-language"),
    ]

    # Packing with max_chapter_bytes=100 ensures Ch 04 does not crowd out Ch 01, Ch 06, and Ch 07
    boxes, captured, total = pack_kdp_boxes(signals, excluded_text="Book Title Subtitle", max_chapter_bytes=100)
    all_packed_text = " ".join(boxes)

    # Ensure box constraints (<= 49 bytes per box)
    for b in boxes:
        assert len(b.encode("utf-8")) <= 49

    # Verify that non-sleep chapters are present in the packed boxes
    assert "folate" in all_packed_text or "prenat" in all_packed_text
    assert "plagiocephaly" in all_packed_text or "cran" in all_packed_text
    assert "speech" in all_packed_text or "vocabul" in all_packed_text


def test_arc79_bucket_fingerprint_deduplication(tmp_path):
    from scripts.marketing_intelligence import import_gkp_export
    import csv

    # Create dummy native GKP export CSV with identical bucket metrics for 2 different queries mapped to Ch 03
    export_csv = tmp_path / "gkp_bucket_test.csv"
    with open(export_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Keyword", "Avg. monthly searches", "Competition", "Competition (indexed value)", "Top of page bid (low range)", "Top of page bid (high range)"])
        # Both queries have volume 12100, comp 0, bid 0.4711 - 8.9545
        writer.writerow(["light therapy for jaundice in newborns", "12100", "Low", "0", "0.471067", "8.9545"])
        writer.writerow(["infant jaundice phototherapy", "12100", "Low", "0", "0.471067", "8.9545"])

    seed_csv = tmp_path / "seed.csv"
    report = import_gkp_export(export_csv, "parenthood-atlas", seed_csv)
    assert "duplicate permutations merged" in report or "keyword row(s) parsed" in report

    # Verify that seed CSV only contains 1 consolidated row instead of 2 redundant rows
    with open(seed_csv, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["query"] in ("light therapy for jaundice in newborns", "infant jaundice phototherapy")




