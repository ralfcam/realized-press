# tests/test_bwe_views.py
"""
End-to-end view integration tests for Realized Press BWE (P-ARC-18).
Validates HTTP responses, DOM structures, navigation tabs, and HTMX endpoints
across /site, /ide, /read/{series}/{chapter}, and /analytics.
"""
import re
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from bwe.main import app


def test_root_redirect(client: TestClient) -> None:
    """GET / must issue an HTTP 307 redirect to /site/ to land on the Imprint Hub."""
    res_no_follow = client.get("/", follow_redirects=False)
    assert res_no_follow.status_code == 307, f"Expected 307 redirect, got {res_no_follow.status_code}"
    assert res_no_follow.headers["location"] == "/site/", (
        f"Expected redirect location '/site/', got {res_no_follow.headers.get('location')}"
    )

    res_followed = client.get("/", follow_redirects=True)
    assert res_followed.status_code == 200, f"Expected 200 after redirect, got {res_followed.status_code}"
    assert "/site/" in str(res_followed.url), f"Final URL should contain /site/, got {res_followed.url}"


def test_site_view(client: TestClient) -> None:
    """GET /site/ must return 200 with brand mark, navigation tabs, catalog/player, and drawer container."""
    res = client.get("/site/", follow_redirects=True)
    assert res.status_code == 200, f"Expected 200 for /site/, got {res.status_code}"
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Brand Mark & Imprint Identity
    brand = (
        soup.find("a", attrs={"aria-label": lambda v: v and "realized press" in v.lower()})
        or soup.find(string=re.compile(r"REALIZED PRESS", re.I))
    )
    assert brand is not None, "Realized Press brand mark missing in /site/"

    # 2. Navigation Tabs (ARIA tablist with Audio tab active)
    nav_tabs = soup.find_all("a", attrs={"role": "tab"})
    assert len(nav_tabs) >= 3, f"Expected at least 3 navigation tabs in nav, found {len(nav_tabs)}"
    active_tab = soup.find("a", attrs={"role": "tab", "aria-selected": "true"})
    assert active_tab is not None, "Expected active selected navigation tab in nav"
    assert "audio" in active_tab.text.lower() or "site" in active_tab.text.lower(), (
        f"Active tab should be Audio/Site on /site/, got '{active_tab.text.strip()}'"
    )

    # 3. Multi-Series Catalog Container
    catalog = (
        soup.find(id="catalog-list")
        or soup.find(id="book-nav-list")
        or soup.find(class_=re.compile(r"catalog|book-list", re.I))
    )
    assert catalog is not None, "Catalog list container (#catalog-list or #book-nav-list) missing in /site/"

    # 4. Audiobook Player Markup
    player = (
        soup.find("audio")
        or soup.find(id="master-audio-player")
        or soup.find(class_=re.compile(r"player|dock", re.I))
    )
    assert player is not None, "Audio player element or container missing in /site/"

    # 5. Public Evidence Brief / Modal Drawer Container
    brief_drawer = (
        soup.find(id="brief-drawer")
        or soup.find(attrs={"data-brief-drawer": True})
        or soup.find(id="site-footnote-drawer")
        or soup.find(attrs={"role": "dialog"})
        or soup.find(class_=re.compile(r"drawer|modal", re.I))
    )
    assert brief_drawer is not None, "Brief drawer or side drawer container missing in /site/"


def test_ide_view(client: TestClient) -> None:
    """GET /ide must return 200 with FTS5 search, card results, audit runner form, and editor/explorer markup."""
    res = client.get("/ide")
    assert res.status_code == 200, f"Expected 200 for /ide, got {res.status_code}"
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Live FTS5 Card Search Input
    search_input = (
        soup.find("input", attrs={"name": "q"})
        or soup.find("input", attrs={"type": "search"})
        or soup.find("input", attrs={"placeholder": re.compile(r"search|doi|okf", re.I)})
    )
    assert search_input is not None, "FTS5 card search input missing in /ide"

    # 2. Evidence Card Results Container
    card_results = (
        soup.find(id="card-results")
        or soup.find(attrs={"data-pane": "cards"})
        or soup.find(id=re.compile(r"card.*result", re.I))
    )
    assert card_results is not None, "Card results container (#card-results) missing in /ide"

    # 3. Epistemic Audit Gate Runner Form
    audit_form = (
        soup.find("form", attrs={"hx-post": "/ide/audit"})
        or soup.find("form", attrs={"action": "/ide/audit"})
        or soup.find("form", attrs={"id": re.compile(r"audit", re.I)})
    )
    assert audit_form is not None, "Epistemic audit runner form targeting /ide/audit missing in /ide"

    # 4. File Explorer Markup / Path Selector
    file_explorer = (
        soup.find(id="file-explorer")
        or soup.find(attrs={"data-pane": "explorer"})
        or soup.find(id="target-path")
        or soup.find("select", attrs={"name": "target_path"})
        or soup.find(attrs={"aria-label": re.compile(r"file|path|explorer", re.I)})
    )
    assert file_explorer is not None, "File explorer markup or target path selector missing in /ide"

    # 5. Split Editor Container / Main Workbench Panel
    editor_container = (
        soup.find(id="editor-container")
        or soup.find(attrs={"data-pane": "editor"})
        or soup.find(class_=re.compile(r"split-editor|workbench", re.I))
        or soup.find("main")
    )
    assert editor_container is not None, "Split editor container or main workbench panel missing in /ide"


def test_reader_view(client: TestClient) -> None:
    """GET /read/{series}/{chapter} must return 200 with #reader-content, 3-lens indicator, takeaways, and footnotes."""
    res = client.get("/read/parenthood-atlas/01-before-the-child-is-born")
    assert res.status_code == 200, f"Expected 200 for reader endpoint, got {res.status_code}"
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Reader Article Content
    article = soup.find("article", attrs={"id": "reader-content"})
    assert article is not None, "Reader manuscript article (#reader-content) missing in reader view"
    assert len(article.text.strip()) > 200, "Reader article content is unexpectedly empty or short"

    # 2. Three-Lens Method Toggle or Epistemic Indicator
    lens_element = (
        soup.find(id="lens-toggle")
        or soup.find(attrs={"data-lens-toggle": True})
        or soup.find(attrs={"aria-label": re.compile(r"lens", re.I)})
        or soup.find(string=re.compile(r"Science.*Interpretation.*Art", re.I))
    )
    assert lens_element is not None, "Three-lens method toggle or epistemic indicator missing in reader view"

    # 3. Takeaway Cards or Container
    takeaway_element = (
        soup.find(id="takeaways")
        or soup.find(attrs={"data-takeaways": True})
        or soup.find(class_=re.compile(r"takeaway", re.I))
        or soup.find("aside", attrs={"aria-label": re.compile(r"feedback|apparatus", re.I)})
        or soup.find("aside")
    )
    assert takeaway_element is not None, "Takeaway cards container missing in reader view"

    # 4. Footnote Integration / Side Drawer Target
    footnote_element = (
        soup.find(id="footnote-drawer")
        or soup.find(id="footnote-drawer-content")
        or soup.find(attrs={"data-footnote-container": True})
        or soup.find(class_=re.compile(r"footnote", re.I))
    )
    assert footnote_element is not None, "Footnote drawer or integration target missing in reader view"


def test_reader_view_404(client: TestClient) -> None:
    """GET /read/{invalid}/{invalid} must return HTTP 404 with appropriate detail."""
    res = client.get("/read/invalid-series-slug/invalid-chapter-slug")
    assert res.status_code == 404, f"Expected 404 for invalid series/chapter, got {res.status_code}"

    res_chapter = client.get("/read/parenthood-atlas/non-existent-chapter-999")
    assert res_chapter.status_code == 404, f"Expected 404 for non-existent chapter, got {res_chapter.status_code}"


def test_analytics_view(client: TestClient) -> None:
    """GET /analytics?series=parenthood-atlas returns 200 with quadrant SVG, chapter volume bars, KDP boxes, sparklines."""
    res = client.get("/analytics?series=parenthood-atlas")
    assert res.status_code == 200, f"Expected 200 for /analytics, got {res.status_code}"
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Demand Quadrant Scatter SVG or Header
    has_quadrant = (
        "Demand vs. BM25 Coverage Quadrant" in res.text
        or "Demand Quadrant" in res.text
        or soup.find(id=re.compile(r"quadrant", re.I))
    )
    assert has_quadrant, "Demand vs BM25 coverage quadrant missing in /analytics"

    # 2. Chapter Volume & CPC Ceiling Bars
    has_volume_bars = (
        "Chapter Volume" in res.text
        or "Volume &amp; CPC" in res.text
        or "Volume & CPC" in res.text
        or soup.find(id=re.compile(r"chapter.*bar", re.I))
    )
    assert has_volume_bars, "Chapter volume bars missing in /analytics"

    # 3. Amazon KDP 7 Backend Keyword Boxes
    has_kdp_boxes = (
        "Amazon KDP 7 Backend Keyword Boxes" in res.text
        or "KDP" in res.text
        or soup.find(id=re.compile(r"kdp", re.I))
    )
    assert has_kdp_boxes, "KDP 7-box utilization section missing in /analytics"

    # 4. SVG Charts & 12-Month Sparklines
    svgs = soup.find_all("svg")
    assert len(svgs) >= 2, f"Expected multiple SVG visualizations in /analytics, found {len(svgs)}"


def test_htmx_endpoints(client: TestClient) -> None:
    """Test essential HTMX partial endpoints: footnote inspection, dashboard refresh, and CSV ads export."""
    # 1. Footnote drawer partial
    fn_res = client.get("/hx/footnote/parenthood-atlas/01-before-the-child-is-born/ch01-folate")
    assert fn_res.status_code == 200, f"Expected 200 for footnote endpoint, got {fn_res.status_code}"
    assert "folic acid" in fn_res.text.lower() or "ch01-folate" in fn_res.text.lower(), (
        "Footnote partial missing expected citation evidence"
    )

    # 2. Analytics dashboard partial
    dash_res = client.get("/hx/analytics/dashboard?series=parenthood-atlas")
    assert dash_res.status_code == 200, f"Expected 200 for dashboard HTMX swap, got {dash_res.status_code}"
    assert "Demand vs. BM25" in dash_res.text or "quadrant" in dash_res.text.lower(), (
        "Dashboard partial missing expected chart markup"
    )

    # 3. Amazon Ads CSV export
    ads_res = client.get("/hx/analytics/export-ads?series=parenthood-atlas")
    assert ads_res.status_code == 200, f"Expected 200 for Ads export, got {ads_res.status_code}"
    assert "text/csv" in ads_res.headers.get("content-type", ""), (
        f"Expected text/csv content-type, got {ads_res.headers.get('content-type')}"
    )
    assert len(ads_res.text.strip()) > 0, "Amazon Ads CSV export returned empty content"

    # 4. Citation telemetry inspection
    telem_res = client.get("/hx/telemetry")
    assert telem_res.status_code == 200, f"Expected 200 for telemetry endpoint, got {telem_res.status_code}"

    # 5. Public Evidence Brief endpoint (if registered in app routes)
    registered_routes = [route.path for route in app.routes]
    if "/hx/brief/{series_slug}/{card_slug}" in registered_routes:
        brief_res = client.get("/hx/brief/parenthood-atlas/prenatal-folate-ntd")
        assert brief_res.status_code in (200, 404), f"Unexpected status for brief endpoint: {brief_res.status_code}"
