# tests/test_adversarial_stress.py
"""
Adversarial Stress Testing & Route Robustness Test Suite for Realized Press BWE.
Author: Challenger 1 (Adversarial Stress Testing)
Verification Gate: Milestone 5

Stress-tests endpoints using FastAPI TestClient across 5 attack vectors:
1. Directory traversal attacks on /ide/file-content and /hx/ide/editor.
2. Malformed / boundary series slugs and chapter slugs (Unicode, SQLi, boundary lengths, glob syntax).
3. Missing query parameters, missing cookies, unexpected HTTP verbs, and unprocessable form bodies.
4. Footnote requests for non-existent footnote IDs, regex injection, SQLi, XSS, and boundary lengths.
5. Analytics endpoints with invalid series, directory traversal, SQLi, and empty series slugs.

Enforces:
All edge cases MUST return appropriate HTTP error codes (e.g. 400, 403, 404, 405, 422) or
graceful safe fallbacks (200), and NEVER trigger unhandled 500 Internal Server Errors.
"""

from pathlib import Path
import shutil
import urllib.parse
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def clean_junk_analytics_dirs():
    """Ensure test artifacts in dist/analytics created by adversarial probes are cleaned up."""
    yield
    dist_dir = REPO_ROOT / "dist" / "analytics"
    if dist_dir.is_dir():
        for p in dist_dir.iterdir():
            if p.is_dir() and p.name not in {"parenthood-atlas", "parenthood-atlas-es", "architectures-of-memory"}:
                shutil.rmtree(p, ignore_errors=True)



# =============================================================================
# VECTOR 1: Directory Traversal Attacks on /ide/file-content & /hx/ide/editor
# =============================================================================

@pytest.mark.parametrize("traversal_path", [
    "../../etc/passwd",
    "..\\..\\secret.txt",
    "../../../../../../../../Windows/win.ini",
    "..\\..\\..\\..\\..\\..\\Windows\\win.ini",
    "C:/Windows/win.ini",
    "C:\\Windows\\win.ini",
    "/etc/passwd",
    "/etc/shadow",
    "series/../../README.md",
    "series/parenthood-atlas/../../../bwe/main.py",
    "series/parenthood-atlas/../../../../bwe/main.py",
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%2f..%2fWindows%2fwin.ini",
    "....//....//....//Windows//win.ini",
    "series/parenthood-atlas/series.yaml",  # Non-markdown file in series
    "series/parenthood-atlas/chapters/nonexistent.md",  # Non-existent markdown in series
    "../nonexistent.md",
])
def test_directory_traversal_rejection(client: TestClient, traversal_path: str):
    """
    Assert that all directory traversal probes and invalid/non-md paths
    are rejected with 404 (or 400) and NEVER trigger an unhandled 500 error.
    """
    for endpoint in ["/ide/file-content", "/hx/ide/editor"]:
        response = client.get(f"{endpoint}?path={urllib.parse.quote(traversal_path)}")
        assert response.status_code in {400, 404}, (
            f"Expected 400/404 for traversal path '{traversal_path}' on {endpoint}, "
            f"got HTTP {response.status_code}: {response.text[:200]}"
        )
        assert response.status_code != 500


def test_directory_traversal_target_path_param(client: TestClient):
    """Verify target_path parameter also rejects directory traversal."""
    response = client.get("/ide/file-content?target_path=../../etc/passwd")
    assert response.status_code in {400, 404}
    assert response.status_code != 500


def test_ide_file_content_valid_baseline(client: TestClient):
    """Verify legitimate chapter markdown path resolves cleanly with 200."""
    response = client.get("/ide/file-content?path=series/parenthood-atlas/chapters/01-before-the-child-is-born.md")
    assert response.status_code == 200
    assert "01-Before-The-Child-Is-Born" in response.text or "Before The Child" in response.text


def test_ide_file_content_json_format(client: TestClient):
    """Verify format=json returns valid JSON payload without server crash."""
    response = client.get(
        "/ide/file-content?path=series/parenthood-atlas/chapters/01-before-the-child-is-born.md&format=json"
    )
    assert response.status_code == 200
    data = response.json()
    assert "raw_content" in data
    assert "preview_html" in data


# =============================================================================
# VECTOR 2: Malformed / Boundary Series Slugs & Chapter Slugs
# =============================================================================

@pytest.mark.parametrize("series_slug,chapter_slug", [
    ("🌟📚", "capítulo-1"),
    ("русский-текст", "глава-1"),
    ("日本語シリーズ", "第1章"),
    ("' OR '1'='1", "01-test"),
    ("parenthood-atlas", "' UNION SELECT 1,2,3--"),
    ("parenthood-atlas", "'; DROP TABLE citation_telemetry; --"),
    ("a" * 300, "01-test"),
    ("parenthood-atlas", "a" * 300),
    ("a" * 1000, "a" * 1000),
    ("..%2f..%2fetc", "passwd"),
    ("parenthood-atlas", "..%2f..%2f..%2fmain"),
    ("parenthood-atlas", "non-existent-chapter-slug-xyz"),
    ("non-existent-series-slug-xyz", "01-before-the-child-is-born"),
    ("parenthood-atlas", "*"),
    ("parenthood-atlas", "["),
    ("parenthood-atlas", "?"),
    ("parenthood-atlas", "{}"),
])
def test_malformed_reader_slugs(client: TestClient, series_slug: str, chapter_slug: str):
    """
    Verify malformed, Unicode, SQLi, glob, and boundary slugs on /read/...
    return 404 (or 200 if legitimate glob match) and NEVER crash with 500.
    """
    encoded_series = urllib.parse.quote(series_slug)
    encoded_chapter = urllib.parse.quote(chapter_slug)
    url = f"/read/{encoded_series}/{encoded_chapter}"
    response = client.get(url)
    assert response.status_code in {200, 404}, (
        f"Expected 200 or 404 for slug pair ({series_slug}, {chapter_slug}), "
        f"got HTTP {response.status_code}: {response.text[:200]}"
    )
    assert response.status_code != 500


@pytest.mark.parametrize("series_slug,card_slug", [
    ("nonexistent", "nonexistent"),
    ("' OR '1'='1", "' OR '1'='1"),
    ("parenthood-atlas", "non-existent-card-9999"),
    ("parenthood-atlas", "["),
    ("parenthood-atlas", "*"),
    ("parenthood-atlas", "a" * 500),
    ("🌟📚", "tarjeta-1"),
])
def test_malformed_brief_slugs(client: TestClient, series_slug: str, card_slug: str):
    """
    Verify /hx/brief/... handles non-existent, SQLi, and boundary slugs gracefully with 404.
    """
    encoded_series = urllib.parse.quote(series_slug)
    encoded_card = urllib.parse.quote(card_slug)
    url = f"/hx/brief/{encoded_series}/{encoded_card}"
    response = client.get(url)
    assert response.status_code in {200, 404}, (
        f"Expected 200 or 404 for brief ({series_slug}, {card_slug}), "
        f"got HTTP {response.status_code}: {response.text[:200]}"
    )
    assert response.status_code != 500


# =============================================================================
# VECTOR 3: Missing Query Parameters, Missing Cookies, Unexpected Verbs
# =============================================================================

def test_missing_query_parameters(client: TestClient):
    """
    Verify endpoints with missing query parameters either use safe defaults (200)
    or return 400 Bad Request, and NEVER 500.
    """
    # /ide/file-content requires path or target_path -> must return 400
    res_ide = client.get("/ide/file-content")
    assert res_ide.status_code == 400
    assert res_ide.status_code != 500

    res_editor = client.get("/hx/ide/editor")
    assert res_editor.status_code == 400
    assert res_editor.status_code != 500

    res_empty_path = client.get("/ide/file-content?path=")
    assert res_empty_path.status_code == 400
    assert res_empty_path.status_code != 500

    # /analytics defaults to parenthood-atlas -> must return 200
    res_analytics = client.get("/analytics")
    assert res_analytics.status_code == 200

    # /hx/analytics/dashboard defaults to parenthood-atlas -> must return 200
    res_dash = client.get("/hx/analytics/dashboard")
    assert res_dash.status_code == 200

    # /hx/analytics/export-ads defaults to parenthood-atlas -> must return 200
    res_export = client.get("/hx/analytics/export-ads")
    assert res_export.status_code == 200

    # /ide/search-cards defaults to q="" -> must return 200
    res_search = client.get("/ide/search-cards")
    assert res_search.status_code == 200


def test_missing_cookies(client: TestClient):
    """Verify that requests without cookies or with empty/garbage cookies work normally."""
    client.cookies.clear()
    res = client.get("/site/")
    assert res.status_code == 200

    # With malformed cookie string in header
    res_cookie = client.get("/site/", headers={"Cookie": "malformed; ==; ;; invalid"})
    assert res_cookie.status_code == 200


@pytest.mark.parametrize("method,endpoint", [
    ("POST", "/site/"),
    ("POST", "/ide"),
    ("POST", "/analytics"),
    ("POST", "/read/parenthood-atlas/01-before-the-child-is-born"),
    ("DELETE", "/site/"),
    ("DELETE", "/ide"),
    ("DELETE", "/analytics"),
    ("PUT", "/ide"),
    ("PUT", "/read/parenthood-atlas/01-before-the-child-is-born"),
    ("GET", "/hx/feedback"),
    ("GET", "/ide/audit"),
    ("GET", "/hx/analytics/write-kdp-yaml"),
])
def test_unexpected_http_verbs(client: TestClient, method: str, endpoint: str):
    """
    Verify that unexpected HTTP verbs return 405 Method Not Allowed, NEVER 500.
    """
    response = client.request(method, endpoint)
    assert response.status_code == 405, (
        f"Expected 405 Method Not Allowed for {method} {endpoint}, "
        f"got HTTP {response.status_code}: {response.text[:200]}"
    )


def test_missing_form_data_on_post(client: TestClient):
    """
    Verify that POST endpoints with missing required Form parameters
    return 422 Unprocessable Entity, NEVER 500.
    """
    # /hx/feedback requires series_slug, chapter_slug, comment
    res_fb = client.post("/hx/feedback", data={})
    assert res_fb.status_code == 422
    assert res_fb.status_code != 500

    # /ide/audit requires script_name, target_path
    res_audit = client.post("/ide/audit", data={})
    assert res_audit.status_code == 422
    assert res_audit.status_code != 500


def test_ide_audit_unsupported_script(client: TestClient):
    """
    Verify that passing an unsupported / arbitrary script name to /ide/audit
    is rejected with 400 Bad Request, preventing arbitrary execution.
    """
    res = client.post("/ide/audit", data={"script_name": "malicious_script", "target_path": "series/"})
    assert res.status_code == 400
    assert "Unsupported audit script" in res.text
    assert res.status_code != 500


# =============================================================================
# VECTOR 4: Footnote Requests for Non-Existent Footnote IDs & Malformed IDs
# =============================================================================

@pytest.mark.parametrize("footnote_id", [
    "non-existent-footnote-99999",
    "' OR '1'='1",
    "'; DROP TABLE citation_telemetry; --",
    "<script>alert('xss')</script>",
    '"><img src=x onerror=alert(1)>',
    ".*",
    "[",
    "(?:.*)",
    "+++",
    "\\\\",
    "^$",
    "a" * 1000,
    "🌟-footnote",
])
def test_footnote_nonexistent_and_malformed_ids(client: TestClient, footnote_id: str):
    """
    Verify that non-existent footnote IDs, SQLi, regex metacharacters,
    and boundary IDs return HTTP 200 with fallback drawer content, NEVER 500.
    """
    encoded_fn = urllib.parse.quote(footnote_id)
    url = f"/hx/footnote/parenthood-atlas/01-before-the-child-is-born/{encoded_fn}"
    response = client.get(url)
    assert response.status_code in {200, 404}, (
        f"Expected 200 fallback or 404 for footnote '{footnote_id}', "
        f"got HTTP {response.status_code}: {response.text[:200]}"
    )
    assert response.status_code != 500



def test_footnote_nonexistent_series_and_chapter(client: TestClient):
    """Verify /hx/footnote returns 404 when chapter or series is not found."""
    res_ch = client.get("/hx/footnote/parenthood-atlas/nonexistent-chapter-xyz/fn1")
    assert res_ch.status_code == 404
    assert res_ch.status_code != 500

    res_series = client.get("/hx/footnote/nonexistent-series-xyz/01-before-the-child-is-born/fn1")
    assert res_series.status_code == 404
    assert res_series.status_code != 500


# =============================================================================
# VECTOR 5: Analytics Export Requests with Invalid Series
# =============================================================================

@pytest.mark.parametrize("invalid_series", [
    "non-existent-series-slug-xyz",
    "../../etc/passwd",
    "'; DROP TABLE citation_telemetry; --",
    "🌟-invalid-series",
    "a" * 200,
])
def test_analytics_invalid_series(client: TestClient, invalid_series: str):
    """
    Verify that passing invalid or malicious series to /analytics,
    /hx/analytics/dashboard, and /hx/analytics/export-ads either safely renders
    fallback analytics or gracefully handles the series without 500 crashes.
    """
    for endpoint in ["/analytics", "/hx/analytics/dashboard", "/hx/analytics/export-ads"]:
        response = client.get(f"{endpoint}?series={urllib.parse.quote(invalid_series)}")
        assert response.status_code in {200, 400, 404}, (
            f"Expected graceful status (200, 400, or 404) for series '{invalid_series}' on {endpoint}, "
            f"got HTTP {response.status_code}: {response.text[:200]}"
        )
        assert response.status_code != 500


def test_analytics_empty_series_param(client: TestClient):
    """Verify empty series parameter does not crash analytics."""
    res = client.get("/analytics?series=")
    assert res.status_code in {200, 400, 404}
    assert res.status_code != 500
