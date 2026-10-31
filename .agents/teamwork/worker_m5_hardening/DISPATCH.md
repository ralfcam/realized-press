# Task Assignment: Worker M5 — Route Hardening & Modal Accessibility Polish

## Working Directory
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m5_hardening\`

## Mission
Implement the 4 targeted resilience and accessibility fixes identified by Challengers 1 & 2:
1. `bwe/main.py`:
   - In `search_evidence_cards`: Prevent unhandled FTS5 syntax crashes on special characters/quotes (`"`, `'`, `*`, `(`, `)`) by sanitizing `q` and wrapping the query execution in `try...except sqlite3.OperationalError:` returning `rows = []`.
   - In `view_analytics`, `hx_analytics_dashboard`, `hx_analytics_export_ads`, and `hx_analytics_write_kdp_yaml`:
     Validate `series` parameter:
     ```python
     base_slug = series.split("/i18n/")[0]
     if not base_slug or not (SERIES_DIR / base_slug).is_dir():
         raise HTTPException(status_code=404, detail=f"Series '{series}' not found")
     ```
     In `hx_analytics_write_kdp_yaml`, verify `(SERIES_DIR / base_slug / "series.yaml").is_file()` before writing.
2. `bwe/analytics.py`:
   - Line 790 (in `export_static_charts`): Guard `cum_vols` check:
     ```python
     if len(cum_vols) > 0 and cum_vols[-1] > 0:
     ```
3. `bwe/templates/partials/brief_drawer.html`:
   - Add `@keydown.escape.window="open = false"` to the modal container for keyboard Escape accessibility.
4. Verification:
   - Run `python -m pytest tests/` (all 46 tests + adversarial tests pass with 0 crashes).
   - Run `python tests/test_ui_compliance.py` (0 violations).

## File Ownership
- `bwe/main.py`
- `bwe/analytics.py`
- `bwe/templates/partials/brief_drawer.html`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Write your report to:
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m5_hardening\handoff.md`
Report back when finished.

## 2026-10-31T12:30:18Z
**Context**: Milestone 5 Route Hardening & Modal Accessibility Polish
**Content**: Status check. Please report on your current progress with the edits in `bwe/main.py`, `bwe/analytics.py`, and `bwe/templates/partials/brief_drawer.html`.
**Action**: Reply with your current status and ETA, and update your progress.md.
