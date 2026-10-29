"""Unit tests for scripts/gads_client.py (Realized Press BWE v0.6.0)."""

import io
from pathlib import Path
import pytest

from scripts.gads_client import (
    EnrichedKeywordMetric,
    GoogleAdsKeywordClient,
    compute_trend_from_histogram,
    decode_export_bytes,
    parse_native_gkp_csv_export,
    parse_volume_value,
)


def test_parse_volume_value_numbers():
    assert parse_volume_value("1000") == (1000, None)
    assert parse_volume_value("1,000") == (1000, None)
    assert parse_volume_value("10 000") == (10000, None)
    assert parse_volume_value("0") == (0, None)
    assert parse_volume_value("") == (0, None)
    assert parse_volume_value("-") == (0, None)


def test_parse_volume_value_ranges():
    assert parse_volume_value("10K - 100K") == (10000, 100000)
    assert parse_volume_value("1K - 10K") == (1000, 10000)
    assert parse_volume_value("100 - 1K") == (100, 1000)
    assert parse_volume_value("1M - 10M") == (1000000, 10000000)


def test_compute_trend_from_histogram():
    # Empty or short list
    assert compute_trend_from_histogram([]) == 0.0

    # Flat volume over 12 months
    flat = [{"year": 2025, "month": m, "searches": 1000} for m in range(1, 13)]
    assert compute_trend_from_histogram(flat) == 0.0

    # Growth: earliest 3 months = 1000, trailing 3 months = 2000 -> +100%
    growing = [
        {"year": 2025, "month": m, "searches": 1000 if m <= 6 else 2000}
        for m in range(1, 13)
    ]
    assert compute_trend_from_histogram(growing) == 100.0

    # Decline: earliest 3 months = 2000, trailing 3 months = 1000 -> -50%
    declining = [
        {"year": 2025, "month": m, "searches": 2000 if m <= 6 else 1000}
        for m in range(1, 13)
    ]
    assert compute_trend_from_histogram(declining) == -50.0

    # Zero base handled safely
    zero_base = [
        {"year": 2025, "month": m, "searches": 0 if m <= 6 else 1000}
        for m in range(1, 13)
    ]
    assert compute_trend_from_histogram(zero_base) == 100.0


def test_decode_export_bytes():
    # UTF-8 without BOM
    data_utf8 = "Keyword\tAvg. monthly searches\npeanut butter baby\t74000\n".encode("utf-8")
    assert "peanut butter baby" in decode_export_bytes(data_utf8)

    # UTF-8 with BOM
    data_utf8_sig = "\ufeffKeyword\tAvg. monthly searches\npeanut butter baby\t74000\n".encode("utf-8-sig")
    assert "peanut butter baby" in decode_export_bytes(data_utf8_sig)

    # UTF-16LE with BOM (standard Google Ads UI CSV export format)
    data_utf16le = "Keyword\tAvg. monthly searches\npeanut butter baby\t74000\n".encode("utf-16")
    assert "peanut butter baby" in decode_export_bytes(data_utf16le)


def test_parse_native_gkp_csv_export_tsv():
    # Simulates Google Ads Keyword Planner UI tab-delimited export
    content = (
        "Keyword\tAvg. monthly searches\tThree month change\tYoY change\tCompetition\tCompetition (indexed value)\tTop of page bid (low range)\tTop of page bid (high range)\n"
        "peanut butter baby\t74,000\t0%\t+28%\tMedium\t42\t0.45\t1.85\n"
        "baby led weaning purees\t10K - 100K\t+10%\t+34%\tLow\t38\t0.30\t1.20\n"
    )
    export = parse_native_gkp_csv_export(content)
    assert len(export.metrics) == 2

    r0 = export.metrics[0]
    assert r0.query == "peanut butter baby"
    assert r0.monthly_volume == 74000
    assert r0.volume_range_high is None
    assert r0.competition_index == 0.42
    assert r0.cpc_low_usd == 0.45
    assert r0.cpc_high_usd == 1.85

    r1 = export.metrics[1]
    assert r1.query == "baby led weaning purees"
    assert r1.monthly_volume == 10000
    assert r1.volume_range_high == 100000
    assert r1.competition_index == 0.38
    assert r1.cpc_low_usd == 0.30
    assert r1.cpc_high_usd == 1.20


def test_parse_native_gkp_csv_export_csv():
    # Simulates standard CSV with quotes and monthly breakdown columns
    content = (
        "Keyword,Avg. monthly searches,Competition (indexed value),Top of page bid (low range),Top of page bid (high range),Searches: Jan 2025,Searches: Feb 2025\n"
        '"vanishing gradient problem",22200,35,$0.50,$2.10,20000,22000\n'
    )
    export = parse_native_gkp_csv_export(content)
    assert len(export.metrics) == 1
    r = export.metrics[0]
    assert r.query == "vanishing gradient problem"
    assert r.monthly_volume == 22200
    assert r.competition_index == 0.35
    assert r.cpc_low_usd == 0.50
    assert r.cpc_high_usd == 2.10
    assert len(r.monthly_histogram) == 2
    assert r.monthly_histogram[0]["month"] == 1
    assert r.monthly_histogram[0]["searches"] == 20000
    assert r.monthly_histogram[1]["month"] == 2
    assert r.monthly_histogram[1]["searches"] == 22000


def test_google_ads_client_unconfigured():
    # When credentials are missing, methods should gracefully return empty results
    client = GoogleAdsKeywordClient(config_path=Path("non_existent_file.yaml"), customer_id="1234567890")
    assert not client.is_configured
    assert client.fetch_historical_metrics(["test keyword"]) == {}
    assert client.generate_keyword_ideas(["test keyword"]) == []


def test_google_ads_client_login_customer_id():
    client = GoogleAdsKeywordClient(customer_id="123-456-7890", login_customer_id="987-654-3210")
    assert client.customer_id == "1234567890"
    assert client.login_customer_id == "9876543210"


def test_check_environment_diagnostics():
    from scripts.gads_client import check_environment
    report = check_environment()
    assert "sdk_installed" in report
    assert "is_available" in report
    assert "customer_id" in report
    assert report["is_available"] is False
