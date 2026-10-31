# tests/test_challenger_layout.py
"""
Empirical verification and stress testing suite by Challenger 2 (Layout Stability & Interaction Challenger).

Scope:
1. Public Evidence Brief drawer: verify trigger attributes, target #brief-drawer, drawer HTML structure, modal accessibility, zero CLS.
2. 3-Pane IDE: #file-explorer, #editor-container, card search, TTS panel markup, and directory traversal security.
3. Serial reader: #lens-toggle buttons, .chapter-takeaway styling, footnote tooltip / drawer interactions, #reader-content layout isolation.
4. Analytics dashboard: #analytics-content min-height container, chart SVGs, KDP 7 boxes, sparklines, CLS prevention.
5. Mobile navigation: responsive classes, touch targets, ARIA tablist/drawer markup.
6. Stress tests & adversarial edge cases: malformed queries, invalid card slugs, path traversals, missing series.
"""
import re
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
import pytest
from fastapi.testclient import TestClient

from bwe.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# =========================================================================
# 1. PUBLIC EVIDENCE BRIEF DRAWER EMPIRICAL TESTS
# =========================================================================

def test_public_evidence_brief_drawer_triggers_and_container(client: TestClient):
    """Verify /site/ contains #brief-drawer and triggers with correct HTMX attributes."""
    res = client.get("/site/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")

    # Verify #brief-drawer container exists with fixed/relative positioning
    drawer_container = soup.find(id="brief-drawer")
    assert drawer_container is not None, "Missing #brief-drawer container in /site/"
    classes = drawer_container.get("class", [])
    assert any(c in classes for c in ("relative", "fixed", "z-50")), (
        f"#brief-drawer container must have high z-index and positioning classes, got {classes}"
    )

    # Inspect brief triggers
    triggers = soup.find_all(lambda tag: tag.has_attr("hx-get") and "/hx/brief/" in tag["hx-get"])
    if triggers:
        for t in triggers:
            assert t.get("hx-target") == "#brief-drawer", f"Trigger hx-target must be #brief-drawer, got {t.get('hx-target')}"
            assert t.get("hx-swap") in ("innerHTML", None), f"Trigger hx-swap should be innerHTML, got {t.get('hx-swap')}"
            assert t.get("aria-label"), f"Trigger button missing aria-label: {t}"


def test_public_evidence_brief_drawer_html_structure(client: TestClient):
    """Verify GET /hx/brief/... returns valid accessible modal drawer with 9 canonical sections."""
    card_files = list((REPO_ROOT / "series" / "parenthood-atlas" / "evidence-cards").glob("*.md"))
    assert len(card_files) > 0, "No evidence cards found in parenthood-atlas"
    test_slug = card_files[0].stem

    res = client.get(f"/hx/brief/parenthood-atlas/{test_slug}")
    assert res.status_code == 200, f"Expected 200 for /hx/brief/parenthood-atlas/{test_slug}, got {res.status_code}"

    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Modal accessibility
    dialog = soup.find(attrs={"role": "dialog"})
    assert dialog is not None, "Brief drawer markup must have role='dialog'"
    assert dialog.get("aria-modal") == "true", "Brief drawer must have aria-modal='true'"
    assert dialog.get("aria-labelledby") == "brief-drawer-title", "Brief drawer must have aria-labelledby='brief-drawer-title'"

    # 2. Drawer title
    title_el = soup.find(id="brief-drawer-title")
    assert title_el is not None, "Brief drawer must contain #brief-drawer-title"
    assert len(title_el.text.strip()) > 0, "#brief-drawer-title is empty"

    # 3. Backdrop and dismiss buttons
    close_btns = soup.find_all(lambda t: t.has_attr("aria-label") and "close" in t["aria-label"].lower())
    assert len(close_btns) >= 1, "Brief drawer must contain at least one close button"
    for btn in close_btns:
        onclick_or_x = btn.get("onclick", "") + " " + btn.get("@click", "")
        assert "brief-drawer" in onclick_or_x, f"Close button must clear #brief-drawer, got {onclick_or_x}"

    # 4. Zero layout shift layout structure (fixed overlay so opening/closing does not alter main page flow)
    assert "fixed" in dialog.get("class", []), "Brief drawer root container must be 'fixed inset-0' to prevent page CLS"


def test_public_evidence_brief_invalid_slug_handling(client: TestClient):
    """Stress test: verify requesting a non-existent brief returns 404 cleanly without 500 error."""
    res = client.get("/hx/brief/parenthood-atlas/non-existent-bogus-card-999")
    assert res.status_code == 404, f"Expected 404 for invalid brief slug, got {res.status_code}"


# =========================================================================
# 2. 3-PANE IDE EMPIRICAL TESTS
# =========================================================================

def test_ide_markup_panes_and_hooks(client: TestClient):
    """Verify /ide renders all 3 panes: #file-explorer, #editor-container, card search, and TTS panel."""
    res = client.get("/ide")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")

    # Pane 1: File Explorer
    explorer = soup.find(id="file-explorer")
    assert explorer is not None, "Missing #file-explorer in /ide"
    assert "aside" in explorer.name, f"Expected #file-explorer to be an <aside>, got <{explorer.name}>"

    # Pane 2: Split Editor
    editor = soup.find(id="editor-container")
    assert editor is not None, "Missing #editor-container in /ide"

    # Pane 3: Card Search
    search_input = soup.find("input", attrs={"name": "q"})
    assert search_input is not None, "Missing card search input name='q' in /ide"
    assert search_input.get("hx-target") == "#card-results", f"Search input target should be #card-results, got {search_input.get('hx-target')}"
    assert search_input.get("hx-get") == "/ide/search-cards", f"Search input hx-get should be /ide/search-cards, got {search_input.get('hx-get')}"

    # TTS Panel Markup
    tab_tts = soup.find(id="tab-tts")
    assert tab_tts is not None, "Missing #tab-tts tab in /ide"
    assert tab_tts.get("role") == "tab", f"#tab-tts must have role='tab', got {tab_tts.get('role')}"
    assert tab_tts.get("aria-controls") == "panel-tts", f"#tab-tts aria-controls must be 'panel-tts', got {tab_tts.get('aria-controls')}"

    panel_tts = soup.find(id="panel-tts")
    assert panel_tts is not None, "Missing #panel-tts in /ide"
    assert panel_tts.get("aria-labelledby") == "tab-tts", f"#panel-tts must have aria-labelledby='tab-tts', got {panel_tts.get('aria-labelledby')}"

    # Terminal output container
    terminal = soup.find(id="tts-terminal")
    assert terminal is not None, "Missing #tts-terminal in /ide"
    sse_mount = soup.find(id="tts-sse-mount")
    assert sse_mount is not None, "Missing #tts-sse-mount in /ide"


def test_ide_file_content_endpoint_and_traversal_defense(client: TestClient):
    """Verify /ide/file-content loads chapter markdown and rejects directory traversal."""
    res = client.get("/ide/file-content?path=series/parenthood-atlas/chapters/01-before-the-child-is-born.md")
    assert res.status_code == 200
    assert "editor-container" in res.text
    assert "preview-panel" in res.text
    assert "markdown-source" in res.text

    # Path traversal attack stress tests
    traversal_attacks = [
        "../../etc/passwd",
        "..\\..\\Windows\\win.ini",
        "/etc/shadow",
        "series/../../main.py",
        "series/../.env",
    ]
    for attack in traversal_attacks:
        res_attack = client.get(f"/ide/file-content?path={attack}")
        assert res_attack.status_code in (400, 404), (
            f"Directory traversal attack '{attack}' was not rejected! Status: {res_attack.status_code}"
        )


def test_ide_card_search_normal_and_empty(client: TestClient):
    """Verify normal and empty query behavior on /ide/search-cards."""
    res = client.get("/ide/search-cards?q=folate")
    assert res.status_code == 200
    assert "card_results" in res.text or "article" in res.text

    res_empty = client.get("/ide/search-cards?q=")
    assert res_empty.status_code == 200


def test_ide_card_search_malformed_query_vulnerability(client: TestClient):
    """Verify malformed queries in /ide/search-cards are sanitized and handled gracefully (HTTP 200)."""
    res = client.get("/ide/search-cards?q=\"\"\"'''")
    assert res.status_code == 200


# =========================================================================
# 3. SERIAL READER EMPIRICAL TESTS
# =========================================================================

def test_serial_reader_layout_and_interaction_hooks(client: TestClient):
    """Verify /read/{series}/{chapter} renders #reader-content, #lens-toggle, .chapter-takeaway, and footnote apparatus."""
    res = client.get("/read/parenthood-atlas/01-before-the-child-is-born")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Reader Article & Grid Layout Isolation
    article = soup.find("article", attrs={"id": "reader-content"})
    assert article is not None, "Missing #reader-content article in reader"
    assert "prose" in article.get("class", []), "#reader-content must have prose typography classes"

    main_el = soup.find("main")
    assert main_el is not None, "Missing <main> tag in reader"
    aside_el = soup.find("aside", attrs={"aria-label": lambda v: v and "apparatus" in v.lower()})
    assert aside_el is not None, "Missing epistemic apparatus <aside> in reader"

    # 2. #lens-toggle buttons
    lens_bar = soup.find(id="lens-toggle")
    assert lens_bar is not None, "Missing #lens-toggle in reader"
    lens_buttons = lens_bar.find_all("button")
    assert len(lens_buttons) >= 3, f"Expected at least 3 lens toggle buttons, found {len(lens_buttons)}"
    for btn in lens_buttons:
        assert btn.get("aria-label"), f"Lens button missing aria-label: {btn}"
        assert ":aria-pressed" in btn.attrs or "aria-pressed" in btn.attrs, f"Lens button missing aria-pressed: {btn}"

    # 3. .chapter-takeaway styling and 3-Tier Causal Resolution
    takeaways = soup.find(class_=re.compile(r"chapter-takeaway")) or soup.find(id="takeaways")
    assert takeaways is not None, "Missing .chapter-takeaway or #takeaways in reader"
    assert "chapter-takeaway" in takeaways.get("class", []), "Takeaway container must have .chapter-takeaway class"
    assert "3-tier" in takeaways.text.lower() or "causal resolution" in takeaways.text.lower() or "takeaways" in takeaways.text.lower(), (
        "Takeaway container missing 3-Tier Causal Resolution branding"
    )

    # 4. Footnote drawer & Tooltip
    fn_drawer = soup.find(id="footnote-drawer")
    assert fn_drawer is not None, "Missing #footnote-drawer in reader"
    fn_content = soup.find(id="footnote-drawer-content")
    assert fn_content is not None, "Missing #footnote-drawer-content in reader"

    fn_tooltip = soup.find(id="footnote-tooltip")
    assert fn_tooltip is not None, "Missing #footnote-tooltip element in reader"


def test_footnote_htmx_endpoint_isolation(client: TestClient):
    """Verify GET /hx/footnote/... loads without page reload and returns structured citation."""
    res = client.get("/hx/footnote/parenthood-atlas/01-before-the-child-is-born/ch01-folate")
    assert res.status_code == 200
    assert "folate" in res.text.lower() or "folic acid" in res.text.lower()

    res_bad = client.get("/hx/footnote/parenthood-atlas/01-before-the-child-is-born/non-existent-fn")
    assert res_bad.status_code == 200
    assert "not found" in res_bad.text.lower()


# =========================================================================
# 4. ANALYTICS DASHBOARD & CLS PREVENTION EMPIRICAL TESTS
# =========================================================================

def test_analytics_layout_stability_and_components(client: TestClient):
    """Verify /analytics contains #analytics-content with min-h-[600px], chart SVGs, KDP 7 boxes, and sparklines."""
    res = client.get("/analytics?series=parenthood-atlas")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. #analytics-content CLS prevention container
    content_container = soup.find(id="analytics-content")
    assert content_container is not None, "Missing #analytics-content container in /analytics"
    classes = content_container.get("class", [])
    has_min_height = any("min-h-" in c for c in classes) or "min-height" in content_container.get("style", "")
    assert has_min_height, f"#analytics-content container MUST define a min-height class to prevent CLS, got {classes}"

    # 2. Chart SVGs
    svgs = soup.find_all("svg")
    assert len(svgs) >= 4, f"Expected multiple SVG visualizations (quadrant, bars, sparklines), found {len(svgs)}"

    # 3. KDP 7 Boxes
    kdp_boxes = soup.find_all(string=re.compile(r"Slot [1-7]"))
    assert len(kdp_boxes) == 7, f"Expected exactly 7 KDP slots, found {len(kdp_boxes)}"

    # Verify copy buttons on KDP boxes have >= 44px
    kdp_copy_btns = soup.find_all(lambda t: t.name == "button" and t.get("aria-label", "").startswith("Copy Slot"))
    assert len(kdp_copy_btns) == 7, f"Expected 7 KDP copy buttons, found {len(kdp_copy_btns)}"
    for btn in kdp_copy_btns:
        combined = " ".join(btn.get("class", []))
        assert "min-h-[44px]" in combined and "min-w-[44px]" in combined, f"KDP copy button missing 44px touch targets: {btn}"


def test_analytics_htmx_dashboard_swap_consistency(client: TestClient):
    """Verify GET /hx/analytics/dashboard returns matching #analytics-dashboard partial."""
    res = client.get("/hx/analytics/dashboard?series=parenthood-atlas")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")

    dash = soup.find(id="analytics-dashboard")
    assert dash is not None, "Dashboard partial must contain #analytics-dashboard root element"


def test_analytics_invalid_series_vulnerability(client: TestClient):
    """Verify navigating to /analytics with an invalid series slug returns 404 gracefully."""
    res = client.get("/analytics?series=bogus_series_slug_test")
    assert res.status_code == 404


# =========================================================================
# 5. MOBILE NAVIGATION & RESPONSIVENESS EMPIRICAL TESTS
# =========================================================================

def test_mobile_navigation_responsive_classes_and_aria(client: TestClient):
    """Verify header partial nav.html has proper mobile responsive classes and ARIA controls."""
    res = client.get("/site/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Header banner
    header = soup.find("header", attrs={"role": "banner"})
    assert header is not None, "Missing <header role='banner'> in navigation"

    # 2. Central ARIA Tablist
    tablist = soup.find("nav", attrs={"role": "tablist"})
    assert tablist is not None, "Missing <nav role='tablist'> in navigation"
    assert tablist.get("aria-label"), "Tablist missing aria-label"

    tabs = tablist.find_all("a", attrs={"role": "tab"})
    assert len(tabs) >= 4, f"Expected 4 navigation tabs (Audio, IDE, Reader, Analytics), found {len(tabs)}"
    for tab in tabs:
        assert tab.get("aria-selected") in ("true", "false"), f"Tab missing aria-selected attribute: {tab}"
        combined = " ".join(tab.get("class", []))
        assert "min-h-[44px]" in combined and "min-w-[44px]" in combined, f"Nav tab missing 44px touch target: {tab}"

    # 3. Mobile Hamburger Toggle Button
    mobile_btn = soup.find("button", attrs={"aria-controls": "mobile-nav-drawer"})
    assert mobile_btn is not None, "Missing mobile menu toggle button with aria-controls='mobile-nav-drawer'"
    assert ":aria-expanded" in mobile_btn.attrs or "aria-expanded" in mobile_btn.attrs, "Mobile button missing aria-expanded binding"
    combined_btn = " ".join(mobile_btn.get("class", []))
    assert "md:hidden" in combined_btn, f"Mobile menu toggle must have 'md:hidden' responsive class, got {combined_btn}"
    assert "min-h-[44px]" in combined_btn and "min-w-[44px]" in combined_btn, "Mobile menu toggle missing 44px touch target"

    # 4. Mobile Drawer Dropdown
    mobile_drawer = soup.find(id="mobile-nav-drawer")
    assert mobile_drawer is not None, "Missing #mobile-nav-drawer dropdown container"
    assert "md:hidden" in mobile_drawer.get("class", []), "#mobile-nav-drawer must have 'md:hidden' responsive class"
