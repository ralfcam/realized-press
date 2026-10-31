# tests/test_analytics.py
"""Unit and integration tests for BWE Visual Analytics Studio (ARC-80)."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from bwe.analytics import (
    gini_coefficient,
    herfindahl_index,
    extract_series_bib_years,
    build_series_analytics_payload,
    compute_series_analytics,
    render_sparkline_svg,
    render_quadrant_svg,
    render_chapter_bars_svg,
    render_bib_decade_svg,
    export_static_charts,
    export_static_analytics_deck,
)
from bwe.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_gini_coefficient_edge_cases():
    assert gini_coefficient([]) == 0.0
    assert gini_coefficient([0.0, 0.0, 0.0]) == 0.0
    assert pytest.approx(gini_coefficient([100.0, 100.0, 100.0, 100.0]), abs=1e-4) == 0.0
    val = gini_coefficient([0.0, 0.0, 0.0, 1000.0])
    assert val > 0.7


def test_herfindahl_index_edge_cases():
    assert herfindahl_index([]) == 0.0
    assert herfindahl_index([0.0]) == 0.0
    assert pytest.approx(herfindahl_index([500.0]), abs=1e-4) == 10000.0
    assert pytest.approx(herfindahl_index([10.0, 10.0, 10.0, 10.0]), abs=1e-4) == 2500.0


def test_extract_series_bib_years():
    years = extract_series_bib_years(REPO_ROOT / "series" / "parenthood-atlas")
    assert len(years) >= 50
    assert all(1900 <= y <= 2030 for y in years)


def test_svg_generators():
    # Sparkline
    spark_svg = render_sparkline_svg([], yoy=15.0, vol=5000, query="test query")
    assert "<svg" in spark_svg
    assert "</svg>" in spark_svg
    assert "polyline" in spark_svg

    # Decade SVG
    decade_svg = render_bib_decade_svg({1990: 5, 2000: 10, 2010: 25, 2020: 30}, 68.7, 37.5)
    assert "<svg" in decade_svg
    assert "Bibliographic Recency" in decade_svg


def test_build_series_analytics_payload_parenthood_atlas():
    data = build_series_analytics_payload("parenthood-atlas", root=REPO_ROOT)
    assert data["series_slug"] == "parenthood-atlas"
    assert data["total_clusters"] >= 1000
    assert data["combined_volume"] > 1_000_000
    assert data["verified_clusters"] > 1000
    assert data["verified_clusters_pct"] > 90.0
    assert 0.0 <= data["gini_verified"] <= 1.0
    assert len(data["breakdown"]) == 15
    assert len(data["kdp_boxes"]) == 7
    assert data["market_readiness"] == "7/7"

    # Verify statistical summaries
    stats = data["series_stats"]
    assert "volume" in stats and stats["volume"]["count"] >= 1000
    assert "coverage" in stats and stats["coverage"]["mean"] > 0.0
    assert "opportunity" in stats
    assert "cpc" in stats

    # Verify KDP 50-byte ceilings
    for b in data["kdp_boxes_meta"]:
        assert b["bytes"] <= 49
        assert b["is_valid"] is True

    # Verify SVGs
    assert "<svg" in data["quadrant_svg"]
    assert "<svg" in data["chapter_bars_svg"]
    assert "<svg" in data["bib_decade_svg"]


def test_build_series_analytics_payload_architectures_of_memory():
    data = build_series_analytics_payload("architectures-of-memory", root=REPO_ROOT)
    assert data["series_slug"] == "architectures-of-memory"
    assert data["is_aom"] is True
    assert data["total_clusters"] >= 50
    assert data["combined_volume"] >= 500_000
    assert len(data["book_meta"]) == 5
    assert data["market_readiness"] == "7/7"
    for b in data["kdp_boxes_meta"]:
        assert b["bytes"] <= 49


def test_export_static_charts(tmp_path):
    res = export_static_charts("parenthood-atlas", tmp_path, root=REPO_ROOT)
    expected_files = [
        "demand_quadrant.png",
        "demand_quadrant.svg",
        "chapter_volume_cpc.png",
        "chapter_volume_cpc.svg",
        "kdp_7box_bytes.png",
        "kdp_7box_bytes.svg",
        "bib_recency.png",
        "bib_recency.svg",
        "analytics_deck.png",
        "analytics_deck.svg",
    ]
    for fname in expected_files:
        p = tmp_path / fname
        assert p.is_file(), f"Missing exported chart: {fname}"
        assert p.stat().st_size > 5000, f"File too small: {fname}"


def test_analytics_web_dashboard():
    client = TestClient(app)

    # 1. Full page
    r = client.get("/analytics?series=parenthood-atlas")
    assert r.status_code == 200
    assert "Series Editorial Analytics" in r.text
    assert "Parenthood: The Atlas" in r.text

    # 2. HTMX dashboard partial
    r_dash = client.get("/hx/analytics/dashboard?series=parenthood-atlas")
    assert r_dash.status_code == 200
    assert "Canonical Clusters" in r_dash.text
    assert "Verified GKP Vol" in r_dash.text

    # 3. HTMX overview backwards compatibility
    r_hx = client.get("/hx/analytics/overview?series=architectures-of-memory")
    assert r_hx.status_code == 200
    assert "Canonical Clusters" in r_hx.text

    # 4. Amazon Ads CSV export
    r_ads = client.get("/hx/analytics/export-ads?series=parenthood-atlas")
    assert r_ads.status_code == 200
    assert "Sponsored Products" in r_ads.text

    # 5. Write KDP YAML action
    r_yaml = client.post("/hx/analytics/write-kdp-yaml?series=parenthood-atlas")
    assert r_yaml.status_code == 200
    assert "SCHEMA VALID" in r_yaml.text
