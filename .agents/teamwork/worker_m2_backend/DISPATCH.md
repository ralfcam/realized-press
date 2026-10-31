## 2026-10-31T11:37:12Z
You are Worker M2 (Backend Routes & Data Bindings) for Realized Press BWE.
Your working directory is: c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m2_backend\

You MUST read the original request file before starting:
c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\ORIGINAL_REQUEST.md

Also read:
- c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_2\handoff.md
- c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\orchestrator\PROJECT.md
- c:\Users\joser\PycharmProjects\realized-press\TEST_READY.md

Scope and File Ownership:
You own exclusively:
- bwe/main.py

Tasks:
1. Implement helper `get_server_info(request: Request) -> dict`:
   returns `{"host": request.url.hostname or "0.0.0.0", "port": request.url.port or 8080}`.
2. In `/site/`:
   - Pass `server_info` and `active_tab: "site"` in context.
   - Query stable OKF cards from `evidence_cards_fts` and pass `evidence_briefs` list in context.
   - Add endpoint `GET /hx/brief/{series_slug}/{card_slug}`: loads the OKF v0.2 evidence card from `series/**/evidence-cards/{card_slug}.md`, parses frontmatter and canonical sections, and renders `partials/brief_drawer.html` (or fallback HTMLResponse if template not found).
3. In `/ide`:
   - Pass `server_info` and `active_tab: "ide"` in context.
   - Build and pass `file_tree` dict (all series, books, chapters, and evidence cards).
   - Add endpoint `GET /ide/file-content` (or `GET /hx/ide/editor?path=...`): safely reads chapter or card markdown (preventing directory traversal), renders preview HTML via markdown, and returns content.
4. In `/read/{series_slug}/{chapter_slug}`:
   - Pass `server_info` and `active_tab: "reader"`.
   - Extract `series.yaml` metadata: `title`, `lenses` (`["Science", "Interpretation", "Art"]` or `["Technical", "Organizational", "Philosophical"]`), `epistemic_contract`.
   - Support `lens` query param.
   - Dual template support: render `reader.html` if it exists, otherwise fall back to `portal.html`.
   - Extract `takeaways` and `footnotes` into context.
   - Add route `@app.get("/read/{series_slug}/{book_slug}/{chapter_slug}")` for multi-book series.
5. In `/analytics`:
   - Ensure `"request": request`, `"server_info": get_server_info(request)`, and `"active_tab": "analytics"` are present in context dictionary.
6. Run `python -m pytest tests/` to confirm all 46 tests pass.
