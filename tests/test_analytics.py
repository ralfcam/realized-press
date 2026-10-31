# tests/test_analytics.py
"""Unit and integration tests for BWE Analytics Engine & Web Dashboard (ARC-80)."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from bwe.analytics import (
    gini_coefficient,
    herfindahl_index,
    extract_series_bib_years,
    compute_series_analytics,
    export_static_analytics_deck,
)
from bwe.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_gini_coefficient_edge_cases():
    # Empty or zero sum
    assert gini_coefficient([]) == 0.0
    assert gini_coefficient([0.0, 0.0, 0.0]) == 0.0

    # Perfect equality
    assert pytest.approx(gini_coefficient([100.0, 100.0, 100.0, 100.0]), abs=1e-4) == 0.0

    # Near total inequality
    val = gini_coefficient([0.0, 0.0, 0.0, 1000.0])
    assert val > 0.7


def test_herfindahl_index_edge_cases():
    assert herfindahl_index([]) == 0.0
    assert herfindahl_index([0.0]) == 0.0

    # Monopoly: 1 firm has 100% of volume -> HHI = 10,000
    assert pytest.approx(herfindahl_index([500.0]), abs=1e-4) == 10000.0

    # 4 equal shares of 25% -> 4 * 25^2 = 2500
    assert pytest.approx(herfindahl_index([10.0, 10.0, 10.0, 10.0]), abs=1e-4) == 2500.0


def test_extract_series_bib_years():
    years = extract_series_bib_years(REPO_ROOT / "series" / "parenthood-atlas")
    assert len(years) >= 50
    assert all(1900 <= y <= 2030 for y in years)


def test_compute_series_analytics():
    data = compute_series_analytics("parenthood-atlas", root=REPO_ROOT)
    assert data["series_slug"] == "parenthood-atlas"
    assert data["total_clusters"] >= 1000
    assert data["combined_volume"] > 1_000_000
    assert data["verified_clusters"] > 1000
    assert data["verified_clusters_pct"] > 90.0
    assert 0.0 <= data["gini_verified"] <= 1.0
    assert len(data["breakdown"]) == 15
    assert len(data["kdp_boxes"]) == 7


def test_export_static_analytics_deck(tmp_path):
    res = export_static_analytics_deck("parenthood-atlas", tmp_path, root=REPO_ROOT)
    assert res["png"].is_file()
    assert res["svg"].is_file()
    assert res["png"].stat().st_size > 100_000
    assert res["svg"].stat().st_size > 50_000


def test_analytics_web_dashboard():
    client = TestClient(app)
    r = client.get("/analytics?series=parenthood-atlas")
    assert r.status_code == 200
    assert "Series Editorial Analytics" in r.text
    assert "Parenthood: The Atlas" in r.text

    r_hx = client.get("/hx/analytics/overview?series=architectures-of-memory")
    assert r_hx.status_code == 200
    assert "Total Demand Reach" in r_hx.text
    assert "architectures-of-memory" in r_hx.text
