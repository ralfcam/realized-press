# Test & QA Verification Survey: Realized Press BWE

## 1. Observation

### 1.1 Existing Test Suite Inventory and Tooling
- Directory `tests/` contains exactly three test files:
  - `tests/test_analytics.py` (151 lines): Unit tests for analytics math (Gini, Herfindahl, bib years), SVG generation, series payloads (`parenthood-atlas`, `architectures-of-memory`), static chart export, and web dashboard endpoints.
  - `tests/test_gads_client.py` (215 lines): Unit tests for Google Ads client configuration, volume parsing, trend calculation, and GKP CSV export decoders.
  - `tests/test_keyword_pipeline.py` (514 lines): Integration tests for KDP 50-byte backend keyword packing, opportunity scoring, SQLite BM25 coverage, stop words, cross-lingual lookups, and chapter-balanced allocations.
- There is **no `tests/conftest.py`** anywhere in the repository.
- Reusable fixtures (`client`, database session, HTML parsers) do not exist. The only fixtures used across the test suite are pytest's built-in `tmp_path` (in `test_analytics.py:102`, `test_keyword_pipeline.py:166`, `test_keyword_pipeline.py:488`).
- Execution via `python -m pytest tests/` or `make test` runs in Python 3.13.1 on win32 (`pytest-8.3.4`, `pluggy-1.6.0`, with plugins `anyio`, `asyncio`, `benchmark`, `cov`, `html`, `json-report`, `mock`, `xdist`).
- Output of `python -m pytest`:
  ```
  ============================= test session starts =============================
  collected 36 items
  tests\test_analytics.py ........                                         [ 22%]
  tests\test_gads_client.py ............                                   [ 55%]
  tests\test_keyword_pipeline.py ................                          [100%]
  ============================= 36 passed in 33.84s =============================
  ```
- Executing `pytest` directly in PowerShell fails with:
  ```
  pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program.
  ```
  because `pytest.exe` is in Python's Scripts folder, whereas `python -m pytest` resolves cleanly.
- `beautifulsoup4` (4.13.4), `lxml` (6.0.2), `fastapi` (0.135.3), and `httpx` (0.28.1) are installed in the Python 3.13 environment.

### 1.2 Current Automated Test Coverage for Core Routes
`fastapi.testclient.TestClient` is imported in only one file (`tests/test_analytics.py:6`), and instantiated in only one test (`test_analytics_web_dashboard` at line 123):
```python
122: def test_analytics_web_dashboard():
123:     client = TestClient(app)
124: 
125:     # 1. Full page
126:     r = client.get("/analytics?series=parenthood-atlas")
127:     assert r.status_code == 200
128:     assert "Series Editorial Analytics" in r.text
129:     assert "Parenthood: The Atlas" in r.text
...
```
Endpoints tested currently:
- `/analytics?series=parenthood-atlas` (HTTP 200, basic string search)
- `/hx/analytics/dashboard?series=parenthood-atlas` (HTTP 200)
- `/hx/analytics/overview?series=architectures-of-memory` (HTTP 200)
- `/hx/analytics/export-ads?series=parenthood-atlas` (HTTP 200)
- `/hx/analytics/write-kdp-yaml?series=parenthood-atlas` (HTTP 200)

Routes with **ZERO** automated tests in `tests/`:
- `GET /` (root redirect to `/site/`)
- `GET /site` and `GET /site/`
- `GET /ide`
- `GET /ide/search-cards`
- `POST /ide/audit`
- `GET /ide/tts-stream/{series_slug}/{chapter_slug}`
- `GET /read/{series_slug}/{chapter_slug}`
- `GET /hx/footnote/{series_slug}/{chapter_slug}/{footnote_id}`
- `GET /hx/telemetry`
- `POST /hx/feedback`

Direct probe of core endpoints via `TestClient(app)` returned:
```python
{
    '/site': 200,  # after follow_redirects=True (307 -> /site/)
    '/ide': 200,
    '/read/parenthood-atlas/01-before-the-child-is-born': 200,
    '/analytics': 200
}
```

### 1.3 Template State vs Acceptance Criteria
1. `/site` (`bwe/templates/site.html`):
   - 1739 lines total. Contains an extensive inline `<style>` block (lines 17–1074) and custom CSS layouts (`.navbar`, `.catalog-sidebar`, `.audio-dock`).
   - Line 1079 includes `{% include "partials/nav.html" %}`.
   - Contains multi-series catalog and audiobook player, but **lacks a dedicated public evidence brief drawer** (only mentioned in meta description tag at line 10).
2. `/ide` (`bwe/templates/ide.html`):
   - 318 lines total. Implements a 3-column split: FTS5 card search (col 1), audit gate runner (col 2), and SSE TTS stream (col 3).
   - **Lacks a file explorer / split Markdown editor** as described in R1 ("3-Pane Epistemic IDE including file explorer, split Markdown editor, and OKF v0.2 Evidence Card live drawer").
   - Line 36 includes `{% include "partials/nav.html" %}`.
3. `/read/{series}/{chapter}` (`bwe/templates/portal.html`):
   - 364 lines total. Template is named `portal.html` in `bwe/templates/`, rendered by `bwe/main.py:216` (`return templates.TemplateResponse("portal.html", ...)`).
   - In `ORIGINAL_REQUEST.md`, it is referred to as `reader.html`.
   - Contains manuscript text (`#reader-content`), persistent mini audio player, isolated footnote drawer target (`#footnote-drawer`), and paragraph feedback form (`/hx/feedback`).
   - **Lacks a 3-lens toggle** (zero instances of "lens" in template) and **lacks takeaway cards** (zero instances of "takeaway"). Footnotes are loaded into a side drawer rather than interactive tooltips.
4. `/analytics` (`bwe/templates/analytics.html` and `partials/analytics_dashboard.html`):
   - `analytics.html` (103 lines) includes `partials/nav.html` and `partials/analytics_dashboard.html`.
   - `analytics_dashboard.html` (303 lines) implements Demand vs BM25 Quadrant SVG, Chapter Volume & CPC bars SVG, KDP 7-box 50-byte utilization gauges, and filterable signal table with 12-month sparklines.
5. Navigation Header (`bwe/templates/partials/nav.html`):
   - 82 lines. Defines brand mark, ARIA tablist for Audio (`/site`), IDE (`/ide`), Reader (`/read/...`), Analytics (`/analytics`), LAN 8080 status badge, and Linear link.

### 1.4 Touch Target Size Audit (44px Rule)
Static code analysis on all template interactive elements (`<a>`, `<button>`, `<input>`, `<select>`, `<textarea>`, `role="tab"`, `role="button"`, `role="slider"`) revealed that **over 35 elements violate the 44px touch target requirement**:
- `partials/nav.html`:
  - Lines 26, 36, 46, 56: Navigation tabs have `min-h-[40px] sm:min-h-[36px]` (fails 44px on all screens).
  - Line 76: Linear ARC link has `min-h-[36px]` (fails 44px).
- `ide.html`:
  - Line 109: Card search input has `sm:min-h-[38px]`.
  - Line 125: Footnote copy button has `min-h-[38px]`.
  - Lines 161, 169, 219: Select dropdowns have `sm:min-h-[36px]`.
- `portal.html`:
  - Line 134: Feedback category select has `sm:min-h-[38px]`.
  - Line 95: Audio scrubber has `h-3` without vertical touch padding.
- `partials/analytics_dashboard.html`:
  - Lines 115–116: PNG/SVG export links have `px-2 py-1` (height ~24px).
  - Lines 142, 149: Amazon Ads CSV export and Write YAML buttons have `py-1.5` (~32px).
  - Line 180: Copy box button has `px-2 py-0.5` (~22px).
  - Lines 210, 213, 221: Search input and filter selects have `py-1.5` (~32px).
- `analytics.html`:
  - Lines 53, 56: Header action links have `px-3 py-2` (~36px).
  - Lines 67, 75, 83: Series switcher buttons have `py-2.5` (~38px).
- `partials/footnote_drawer.html`:
  - Line 5: Close drawer button has `p-1.5` (~28px).

### 1.5 WCAG 2.1 AA Color Contrast Analysis
Relative luminance calculations ($L = 0.2126 R_{lin} + 0.7152 G_{lin} + 0.0722 B_{lin}$) and contrast ratios ($(L_1 + 0.05)/(L_2 + 0.05)$) for the design system palette:
- Dark Backgrounds: `stone-950` (#0c0a09), `stone-900` (#1c1917), `stone-800` (#292524).
- High Contrast Text (PASS WCAG AA for all text ≥ 4.5:1):
  - `stone-100` on `stone-950`: **18.11:1**
  - `stone-200` on `stone-950`: **15.73:1**
  - `stone-300` on `stone-950`: **13.26:1**
  - `stone-400` on `stone-950`: **7.83:1** (on `stone-900`: 6.93:1, on `stone-800`: 6.01:1)
  - `amber-400` on `stone-950`: **11.83:1**
  - `amber-500` on `stone-950`: **9.20:1**
  - `amber-300` on `stone-950`: **13.70:1**
  - `emerald-400` on `stone-950`: **10.28:1**
  - `rose-400` on `stone-950`: **7.34:1**
  - `stone-950` text on `amber-500` badge: **9.20:1**
  - `stone-950` text on `amber-600` button: **6.20:1**
- Non-Compliant Low Contrast Tokens (FAIL WCAG AA for normal text < 4.5:1):
  - `stone-500` (#78716c) on `stone-950`: **4.12:1** (fails 4.5:1; only qualifies for large text ≥ 18pt / 14pt bold).
  - `stone-500` on `stone-900`: **3.65:1** (fails 4.5:1).
  - `stone-500` on `stone-800`: **3.16:1** (fails 4.5:1).
  - `stone-600` (#57534e) on `stone-950`: **2.59:1** (fails all WCAG criteria).
- Findings in Templates:
  - `partials/analytics_dashboard.html`: 8 instances of `text-stone-500` on small text (`text-[10px]`, `text-[11px]`).
  - `analytics.html`: Line 97 footer text uses `text-stone-500`.
  - `ide.html`: Line 134 empty state message uses `text-xs text-stone-500`.
  - `partials/telemetry_table.html`: 3 instances of `text-stone-500`.
  - Replacing `text-stone-500` with `text-stone-400` immediately restores 100% WCAG 2.1 AA compliance (jumping from 3.65:1–4.12:1 to 6.93:1–7.83:1).

---

## 2. Logic Chain

1. **Test Infrastructure Baseline**:
   - Observations 1.1 and 1.2 demonstrate that while unit/integration testing for the Python marketing and analytics algorithms is thorough (36 tests), the web application layer has almost zero test coverage (only 1 test function calling TestClient for `/analytics`).
   - The lack of `conftest.py` prevents clean test authoring for new endpoint tests because each test file would need to duplicate `app` imports and `TestClient` instantiation.
   - Therefore, introducing `tests/conftest.py` with standard `client` and `db_session` fixtures is the prerequisite step for all subsequent view testing.

2. **Endpoint and View Verification Gap**:
   - The Acceptance Criteria require automated tests confirming that endpoints `/site`, `/ide`, `/read/{series}/{chapter}`, and `/analytics` return HTTP 200 with rendered elements intact.
   - Observation 1.2 shows that `/site`, `/ide`, and `/read/...` currently have zero tests.
   - Observation 1.3 reveals that `bwe/main.py` serves `portal.html` rather than `reader.html`, and that several required UI elements (public brief drawer, 3-lens toggle, takeaway cards) are absent from the existing templates.
   - Therefore, a dedicated test file `tests/test_bwe_views.py` must be created to assert HTTP status codes (200, 307 redirect, 404 for non-existent chapters) and verify that required elements and components are rendered in the HTML response.

3. **Touch Target Size Verification Gap**:
   - The Acceptance Criteria require static code inspection checking template markup and Tailwind utility classes for 44px touch targets (`min-h-[44px]`, `min-w-[44px]`).
   - Observation 1.4 confirms that more than 35 interactive elements violate this requirement, often dropping to `sm:min-h-[36px]` or relying on `py-1.5`.
   - Therefore, a static audit script and an automated pytest test (`tests/test_ui_compliance.py::test_touch_target_sizes`) must parse the HTML files with `BeautifulSoup`, identify all interactive elements, and assert the presence of `min-h-[44px]`, `min-w-[44px]`, or equivalent 44px Tailwind dimensions (`h-11`, `w-11`, `h-12`).

4. **WCAG 2.1 AA Contrast Verification Gap**:
   - The Acceptance Criteria require static verification that text and UI elements meet WCAG 2.1 AA (4.5:1 for normal text).
   - Observation 1.5 proves mathematically that `stone-500` and `stone-600` fail this threshold on `stone-950` / `stone-900` / `stone-800` backgrounds, and identifies 12+ specific occurrences in `analytics.html`, `partials/analytics_dashboard.html`, and `ide.html`.
   - Therefore, an automated static test (`tests/test_ui_compliance.py::test_wcag_color_contrast`) must compute the contrast ratios and scan template class lists to forbid low-contrast text utilities (`text-stone-500`, `text-stone-600`) on dark backgrounds, enforcing `text-stone-400` or higher.

---

## 3. Caveats

1. **Template Naming Discrepancy**:
   - `ORIGINAL_REQUEST.md` specifies `/read/{series}/{chapter}` (`reader.html`).
   - The codebase currently has `bwe/templates/portal.html`, and `bwe/main.py:216` explicitly references `"portal.html"`.
   - If the implementation refactor creates `reader.html` and re-routes `main.py`, tests should check for `reader.html` (or test the endpoint directly regardless of underlying template name).
2. **Dynamic Client-Side vs Static Render**:
   - `site.html` loads book catalog data and audiobook tracks dynamically via client-side JavaScript (`fetch('/media/...')` and DOM generation in `book-nav-list`).
   - Static inspection and `TestClient` verify server-rendered Jinja2 templates, context injection, and initial DOM. They do not execute full browser JavaScript runtime events (which would require Playwright or Selenium).
3. **Tailwind CDN vs Precompiled CSS**:
   - The templates currently link `<script src="https://cdn.tailwindcss.com"></script>` in the head instead of a static compiled CSS bundle.
   - Static class inspection evaluates the literal utility classes in HTML markup, not computed layout bounding boxes in a headless browser.

---

## 4. Conclusion

1. **Current Test Status**:
   - The test suite contains 36 passing tests focused strictly on marketing and analytics logic.
   - Endpoint test coverage for the BWE application is essentially non-existent: 0% coverage for `/site`, `/ide`, `/read/{series}/{chapter}`, and only superficial string checks for `/analytics`.
2. **Current UI/UX Compliance Status**:
   - Touch targets in navigation and controls fail the 44px threshold in over 35 places.
   - Color contrast fails WCAG 2.1 AA in at least 12 places where `text-stone-500` is used for body or metadata text on `stone-950`/`stone-900` surfaces.
3. **Required QA Deliverables**:
   - **`tests/conftest.py`**: Provide reusable `client` fixture.
   - **`tests/test_bwe_views.py`**: E2E integration test suite covering all 4 views (`/site`, `/ide`, `/read/{series}/{chapter}`, `/analytics`), verifying HTTP 200, redirects, 404 handling, and key rendered DOM elements.
   - **`tests/test_ui_compliance.py`**: Static audit test suite checking 44px touch targets (`min-h-[44px]`, `min-w-[44px]`), WCAG 2.1 AA color contrast compliance, and dark mode palette consistency.
   - **`scripts/audit_ui_accessibility.py`**: Standalone CLI script for fast linting of templates before commit, with optional `make audit-ui` target.

---

## 5. Verification Method

### 5.1 Independent Verification Commands
1. Run existing test suite to verify baseline:
   ```powershell
   python -m pytest tests/ -v
   ```
2. Run newly recommended view tests (once implemented):
   ```powershell
   python -m pytest tests/test_bwe_views.py -v
   ```
3. Run newly recommended static UI compliance tests (once implemented):
   ```powershell
   python -m pytest tests/test_ui_compliance.py -v
   ```
4. Run standalone touch target and contrast diagnostic scripts developed during this survey:
   ```powershell
   python .agents/teamwork/explorer_survey_3/check_touch_targets.py
   python .agents/teamwork/explorer_survey_3/check_contrast_tokens.py
   ```

### 5.2 Recommended Test Files Specification

#### A. `tests/conftest.py`
```python
import pytest
from fastapi.testclient import TestClient
from bwe.main import app
from bwe.db import init_db
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db(REPO_ROOT)

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
```

#### B. `tests/test_bwe_views.py`
```python
from bs4 import BeautifulSoup
import pytest

def test_root_redirect(client):
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 307
    assert res.headers["location"] == "/site/"

def test_site_view(client):
    res = client.get("/site/", follow_redirects=True)
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")
    # Verify Brand & Nav
    assert soup.find("a", attrs={"aria-label": "Realized Press Home"})
    nav_tab = soup.find("a", attrs={"role": "tab", "aria-selected": "true"})
    assert nav_tab and "Audio" in nav_tab.text
    # Verify Audiobook player & catalog containers
    assert soup.find(id="catalog-list") or soup.find(id="book-nav-list")
    assert soup.find("audio") or soup.find(id="master-audio-player")
    # Verify Public Evidence Brief component
    assert soup.find(id="brief-drawer") or soup.find(attrs={"data-brief-drawer": True})

def test_ide_view(client):
    res = client.get("/ide")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")
    # Verify 3-pane elements
    assert soup.find("input", attrs={"name": "q"})
    assert soup.find(id="card-results")
    assert soup.find("form", attrs={"hx-post": "/ide/audit"})
    assert soup.find(id="audit-output")

def test_reader_view(client):
    res = client.get("/read/parenthood-atlas/01-before-the-child-is-born")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")
    # Verify typography, 3-lens toggle, takeaway cards, footnote integration
    assert soup.find("article", attrs={"id": "reader-content"})
    assert soup.find(attrs={"data-lens-toggle": True}) or soup.find(id="lens-toggle")
    assert soup.find(id="footnote-drawer")
    assert soup.find("form", attrs={"hx-post": "/hx/feedback"})

def test_reader_view_404(client):
    res = client.get("/read/non-existent-series/non-existent-chapter")
    assert res.status_code == 404

def test_analytics_view(client):
    res = client.get("/analytics?series=parenthood-atlas")
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "html.parser")
    assert "Demand vs. BM25 Coverage Quadrant" in res.text
    assert "Amazon KDP 7 Backend Keyword Boxes" in res.text
    assert soup.find("svg")  # Chart SVGs rendered
```

#### C. `tests/test_ui_compliance.py`
```python
import re
from pathlib import Path
from bs4 import BeautifulSoup
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "bwe" / "templates"

TOUCH_TARGET_REGEX = re.compile(
    r"min-h-\[44px\]|min-w-\[44px\]|\b(?:h-11|w-11|h-12|w-12|h-14|h-16)\b|min-height:\s*44px|height:\s*44px"
)
LOW_CONTRAST_TEXT_REGEX = re.compile(r"\btext-(stone|zinc|gray|slate)-(500|600|700)\b")

def test_touch_target_sizes():
    interactive_tags = {"a", "button", "input", "select", "textarea"}
    violations = []

    for html_file in TEMPLATES_DIR.rglob("*.html"):
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        elements = soup.find_all(
            lambda t: t.name in interactive_tags
            or t.get("role") in ("button", "tab", "slider")
            or t.get("onclick")
        )
        for el in elements:
            # Skip hidden inputs or elements with hidden class
            if el.name == "input" and el.get("type") == "hidden":
                continue
            cls = " ".join(el.get("class", []))
            style = el.get("style", "")
            if not TOUCH_TARGET_REGEX.search(f"{cls} {style}"):
                rel = html_file.relative_to(TEMPLATES_DIR)
                violations.append(f"{rel}: <{el.name} role='{el.get('role')}'> class='{cls[:50]}'")

    assert not violations, f"Found {len(violations)} elements missing 44px touch targets:\n" + "\n".join(violations[:15])

def test_wcag_color_contrast():
    violations = []
    for html_file in TEMPLATES_DIR.rglob("*.html"):
        lines = html_file.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            if LOW_CONTRAST_TEXT_REGEX.search(line):
                rel = html_file.relative_to(TEMPLATES_DIR)
                violations.append(f"{rel}:{idx} {line.strip()[:60]}")

    assert not violations, f"Found {len(violations)} low-contrast text tokens (e.g. text-stone-500):\n" + "\n".join(violations[:15])
```

### 5.3 Invalidation Conditions
This report's conclusions are invalidated if:
1. `bwe/templates/` is converted to a headless Single Page Application (e.g. React/Vue) rather than FastAPI Jinja2 + HTMX server-rendered templates.
2. The design system abandons `stone-950` dark mode in favor of a light mode palette where `text-stone-500` would achieve sufficient contrast against a light background.
3. Apple / WCAG relaxes the 44px touch target guideline down to 24px (WCAG 2.2 AA minimal size exception), though the task prompt explicitly mandates `min-h-[44px]` and `min-w-[44px]`.
