# Adversarial Stress Testing & Robustness Handoff Report

**Agent:** Challenger 1 (Adversarial Stress Testing & Route Robustness)  
**Milestone:** M5 — Final Verification & Hardening Gate (`P-ARC-18`)  
**Timestamp:** 2026-10-31T12:16:00Z  
**Verdict:** **REQUEST_CHANGES**

---

## 1. Observation

A dedicated adversarial stress harness was authored in `tests/test_adversarial_stress.py` containing 80 empirical test probes executed against the FastAPI application via `TestClient`.

### 1.1 Empirical Test Results Summary
- **Total Adversarial Probes:** 80
- **Passed Edge Cases:** 74 tests (Directory traversal rejection, Unicode/SQLi reader slug handling, HTTP verb restrictions, missing query/form parameter validation, footnote fallback drawer rendering).
- **Failed Edge Cases (Bugs Discovered):** 6 tests (Unhandled 500 server crashes and unhandled exceptions on `/analytics`).
- **Baseline Test Suite:** 45/46 tests passed in full isolation; 1 failure observed under concurrent execution due to SQLite database file locking.

### 1.2 Verbatim Observations & Errors

#### Finding 1: Unhandled Server Crash (`IndexError` -> HTTP 500) on `/analytics?series=<invalid>`
**Trigger Command:**
```powershell
python -c "from fastapi.testclient import TestClient; from bwe.main import app; import shutil, pathlib; p = pathlib.Path('dist/analytics/fresh_invalid_series'); shutil.rmtree(p, ignore_errors=True); c = TestClient(app); r = c.get('/analytics?series=fresh_invalid_series'); print('Status:', r.status_code)"
```
**Verbatim Traceback:**
```text
  File "C:\Users\joser\PycharmProjects\realized-press\bwe\main.py", line 901, in view_analytics
    export_static_charts(series, deck_target, root=REPO_ROOT, lang=lang)
  File "C:\Users\joser\PycharmProjects\realized-press\bwe\analytics.py", line 790, in export_static_charts
    if cum_vols[-1] > 0:
       ~~~~~~~~^^^^
IndexError: index -1 is out of bounds for axis 0 with size 0
```
When an unregistered, invalid, or mistyped `series` parameter is queried (e.g. `series="fresh_invalid_series"`, `series="non-existent-series-slug-xyz"`, `series=""`), `bwe/main.py:901` executes `export_static_charts`. In `bwe/analytics.py:790`, `breakdown` has 0 items, causing `cum_vols` to be an empty NumPy array (`size 0`), crashing with an unhandled `IndexError` that bubbles up as an unhandled HTTP 500 error.

#### Finding 2: Unhandled Server Crash (`FileNotFoundError: [WinError 3]` -> HTTP 500) on Long Series Slugs
**Trigger Request:**
`GET /analytics?series=aaaaaaaaaaaaaaaaaaaaaaaaa...` (200 characters)
**Verbatim Traceback:**
```text
  File "C:\Users\joser\PycharmProjects\realized-press\bwe\main.py", line 901, in view_analytics
    export_static_charts(series, deck_target, root=REPO_ROOT, lang=lang)
  File "C:\Users\joser\PycharmProjects\realized-press\bwe\analytics.py", line 655, in export_static_charts
    output_dir.mkdir(parents=True, exist_ok=True)
  File "C:\Python313\Lib\pathlib\_local.py", line 722, in mkdir
    os.mkdir(self, mode)
FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\Users\\joser\\PycharmProjects\\realized-press\\dist\\analytics\\aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
```
The unvalidated string is passed into `mkdir(parents=True)` which exceeds path limits on Windows filesystem operations, raising an unhandled `FileNotFoundError` (HTTP 500).

#### Finding 3: Arbitrary Directory Pollution in `dist/analytics/`
Inspection of `dist/analytics/` after adversarial probes revealed directories created directly from untrusted query parameters:
```json
{"name":"'; DROP TABLE citation_telemetry; __", "isDir":true}
{"name":".._.._etc_passwd", "isDir":true}
{"name":"fresh_invalid_series", "isDir":true}
{"name":"non_existent_series_slug_xyz", "isDir":true}
{"name":"🌟_invalid_series", "isDir":true}
```
Any caller can induce directory creation under `dist/analytics/` without authentication or series registration checks.

#### Finding 4: Concurrency Race Condition (`sqlite3.OperationalError: database is locked`)
**Trigger Context:**
When two processes run `TestClient(app)` lifespan hooks concurrently (e.g., during parallel testing or multi-worker starts).
**Verbatim Traceback:**
```text
bwe\main.py:304: in lifespan
    init_db(REPO_ROOT)
bwe\db.py:161: in init_db
    _init_db_conn(c, root)
bwe\db.py:206: in _init_db_conn
    reindex_evidence_cards(conn, repo_root)
bwe\db.py:270: in reindex_evidence_cards
    conn.execute("DELETE FROM evidence_cards_fts;")
E   sqlite3.OperationalError: database is locked
```
`bwe/main.py:304` executes `init_db(REPO_ROOT)` on every lifespan entry, which unconditionally issues `DELETE FROM evidence_cards_fts;` and re-indexes all markdown files with exclusive SQLite write locks. When multiple workers or test fixtures execute simultaneously, one process fails with `database is locked`.

#### Robust Passing Controls Observed:
1. **Directory Traversal Rejection:**
   18 probes against `/ide/file-content` and `/hx/ide/editor` (`../../etc/passwd`, `..\..\secret.txt`, `C:\Windows\win.ini`, `/etc/shadow`, `%2e%2e`, `series/parenthood-atlas/../../../bwe/main.py`) were rejected with HTTP 400 or 404. Zero traversal leaks.
2. **Reader Slug Fuzzing:**
   Unicode slugs (`🌟📚`, `русский-текст`, `日本語シリーズ`), SQL injection strings (`' OR '1'='1`, `'; DROP TABLE...`), boundary lengths (300 to 1000 characters), and glob syntax (`*`, `[`, `?`, `{}`) on `/read/{series}/{chapter}` and `/hx/brief/...` returned HTTP 404 (or 200 on valid matches) with zero 500 crashes.
3. **HTTP Verb & Form Validation:**
   POST to GET routes, DELETE, and PUT return HTTP 405 Method Not Allowed. Missing form bodies on POST `/hx/feedback` and `/ide/audit` return HTTP 422. Unsupported scripts on `/ide/audit` return HTTP 400.
4. **Footnote Isolation:**
   Non-existent footnote IDs, SQLi strings, and regex metacharacters return HTTP 200 with fallback drawer markup (`Footnote definition not found in ## Notes.`). Parameterized SQL queries protect SQLite telemetry against injection.

---

## 2. Logic Chain

1. **Premise 1 (Routing Protocol):** The dispatch instructions require that all edge cases return appropriate HTTP error codes (e.g. 400, 403, 404) and NEVER trigger unhandled 500 server crashes.
2. **Observation 1 (Missing Parameter Validation):** In `bwe/main.py` lines 889, 918, 950, and 975, the route handlers for `/analytics`, `/hx/analytics/dashboard`, `/hx/analytics/export-ads`, and `/hx/analytics/write-kdp-yaml` accept `series: str` as a query parameter without verifying if `series` corresponds to a registered directory in `series/<series_slug>/`.
3. **Observation 2 (Directory Creation):** In `bwe/main.py:898-900`, `deck_dir` is computed using string replacements on `series`, and `deck_target = DIST_ANALYTICS_DIR / deck_dir` is passed to `export_static_charts`. In `bwe/analytics.py:655`, `output_dir.mkdir(parents=True, exist_ok=True)` attempts to create this directory. When `series` is an excessively long string (200+ characters), Windows filesystem limits trigger `FileNotFoundError: [WinError 3]`, which is unhandled and results in an HTTP 500 crash.
4. **Observation 3 (Cold-Cache Breakdown IndexError):** When `series` is not found, `build_series_analytics_payload` returns an empty `breakdown = []`. In `bwe/analytics.py:790`, `export_static_charts` accesses `cum_vols[-1]` on an empty NumPy array `cum_vols = np.cumsum(sorted_vols)`. This raises `IndexError: index -1 is out of bounds for axis 0 with size 0`.
5. **Observation 4 (Cache Masking Defect):** Because `export_static_charts` writes `demand_quadrant.svg` (chart 1) before crashing on `analytics_deck` (chart 5), line 900 in `bwe/main.py` (`if not (deck_target / "demand_quadrant.svg").exists():`) skips chart generation on the second call. This deceptively returns 200 on subsequent requests, masking the fatal 500 crash that occurs on any cold-cache or newly requested invalid series.
6. **Observation 5 (Lifespan DB Locking):** In `bwe/main.py:304`, `init_db(REPO_ROOT)` is run on every application lifespan startup. In `bwe/db.py:270` and `300`, `init_db` wipes and rebuilds FTS tables (`DELETE FROM evidence_cards_fts; DELETE FROM chapters_fts;`). When multiple requests or test runners initialize the application concurrently, an unhandled `sqlite3.OperationalError: database is locked` crash occurs.
7. **Deduction:** Because the system triggers unhandled 500 server crashes on invalid series inputs and experiences SQLite lock crashes during concurrent startup, it fails Requirement 2 of the Challenger dispatch. Therefore, the system cannot be approved in its current state.

---

## 3. Caveats

- **Implementation Code Not Modified:** In accordance with the Review-Only constraint, Challenger 1 has not modified any production implementation files (`bwe/main.py`, `bwe/analytics.py`, `bwe/db.py`). Only the stress test harness `tests/test_adversarial_stress.py` was authored.
- **DDoS / Socket Saturation:** High-concurrency socket exhaustion and network-level DDoS resistance were not evaluated; testing focused on application-level routing robustness, input validation, and crash resilience.
- **Footnote Encoded Slash (`%2F`):** When a footnote ID contains a literal slash, Starlette routing treats it as a path segment and returns 404 Not Found. This behavior is safe (no crash/500), but client callers should avoid unquoted slashes in footnote IDs.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

The Book Writing Environment (BWE) demonstrates strong, hardened protections against directory traversal attacks, URL path traversal, and malicious reader/chapter slugs. However, it exhibits critical crash vulnerabilities on the `/analytics` endpoints and concurrency lock collisions in SQLite initialization.

### Action Items for Implementers:
1. **Validate `series` Parameter in `bwe/main.py`:**
   At the start of `view_analytics` (line 889), `hx_analytics_dashboard` (line 920), `hx_analytics_export_ads` (line 950), and `hx_analytics_write_kdp_yaml` (line 975):
   Check whether `(SERIES_DIR / series.split("/i18n/")[0]).is_dir()` exists.
   If not, raise an HTTP 404 error:
   ```python
   base_slug = series.split("/i18n/")[0]
   if not (SERIES_DIR / base_slug).is_dir():
       raise HTTPException(status_code=404, detail=f"Series '{series}' not found")
   ```
2. **Defensive Guard in `bwe/analytics.py` (Line 790):**
   In `export_static_charts`, guard against empty `cum_vols`:
   ```python
   # Replace: if cum_vols[-1] > 0:
   if len(cum_vols) > 0 and cum_vols[-1] > 0:
   ```
3. **Decouple Full Reindexing from Application Lifespan (`bwe/main.py:304` & `bwe/db.py`):**
   Modify `lifespan` in `bwe/main.py` so that `init_db(REPO_ROOT)` only executes schema migrations (`_migrate`) and creates tables if they do not exist, without executing unconditional `DELETE FROM evidence_cards_fts;` and `reindex_evidence_cards` on every application worker start.

---

## 5. Verification Method

To independently verify these findings:

1. **Execute Cold-Cache Crash Reproduction:**
   ```powershell
   python -c "from fastapi.testclient import TestClient; from bwe.main import app; import shutil, pathlib; p = pathlib.Path('dist/analytics/test_crash_probe'); shutil.rmtree(p, ignore_errors=True); c = TestClient(app); r = c.get('/analytics?series=test_crash_probe'); print('Status:', r.status_code)"
   ```
   *Expected Current Result:* Crashes with `IndexError: index -1 is out of bounds for axis 0 with size 0` at `bwe/analytics.py:790`.

2. **Execute Long Path Crash Reproduction:**
   ```powershell
   python -c "from fastapi.testclient import TestClient; from bwe.main import app; c = TestClient(app); r = c.get('/analytics?series=' + 'a'*200); print('Status:', r.status_code)"
   ```
   *Expected Current Result:* Crashes with `FileNotFoundError: [WinError 3] The system cannot find the path specified`.

3. **Execute Full Adversarial Stress Suite:**
   ```powershell
   python -m pytest tests/test_adversarial_stress.py -v
   ```
   *Expected Current Result:* 74 passed, 6 failed (the 6 failures confirm the unhandled 500 errors on invalid series).

4. **Invalidation Condition:**
   Once the recommended mitigations in `bwe/main.py` and `bwe/analytics.py` are implemented, all 80 tests in `tests/test_adversarial_stress.py` will pass with HTTP 404 status codes and 0 server crashes.
