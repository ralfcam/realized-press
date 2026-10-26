# Realized Press Book Writing Environment (BWE) Rules

## 1. Master 4-Stage Execution Sequence
1. **Stage 1 (Immediate Goal — Priority 1: Urgent):** Loop on refinement passes until commercial publication for **Parenthood: The Atlas — Series (`P-ARC-17`)** — *harden and reflect upon the BWE harness along this phase*.
2. **Stage 2 (Priority 2: High):** Repeat the hardened loop for the full 5-book series **Architectures of Memory — Series (`P-ARC-8`)**.
3. **Stage 3 (Priority 3: Medium):** Continue in pillar order of **Realized Press — Canonical Vision & Book Writing Environment (`P-ARC-18`)**.
4. **Stage 4 (Expansion):** Select new series/books driven by **Marketing Intelligence** (`scripts/marketing_intelligence.py`) and publish the internally developed marketing & serial-membership site.

## 2. Definitive 5-Step Tool Routing Protocol
All research, evidence card authoring, verification, and drafting tasks MUST follow this 5-step routing protocol:
1. **Phase 1 — Broad Historical & Archival Synthesis:** Use `perplexity_research` for chapter-level surveys, multi-paper timelines, and cohort histories; use `perplexity_ask` for targeted 2–3 paper lookups.
2. **Phase 2 — Methodological, Confounding & Vendor-Statistic Audits:** Use `perplexity_reason` to audit genetically-informed (GI) cohort confounding, sample populations, and citation decay. For pre-DOI print/literary loci, pair `perplexity_search` with Gemini `search_web`.
3. **Phase 3 — Live Technical Frameworks, Vector Stores & Privacy SDKs:** Run `context7` MCP (`resolve-library-id` → `query-docs`) for authoritative documentation and SDK signatures.
4. **Phase 4 — Mandatory Bibliographic Lock & OKF v0.2 Evidence Cards:**
   - Pass every academic paper through `academic-bib` MCP (`crossref_lookup`, `arxiv_search`, `openalex_work`) to verify DOIs, pagination, and retraction flags (`is_retracted`).
   - Persist to `sources.bib` via `add_bibtex_entry` and synchronize `SOURCES.md` via `python scripts/sync_okf_sources.py`.
   - Author empirical claims in `evidence-cards/*.md` (9 required sections including `## What This Does Not Mean`).
   - Never commit raw `vertexaisearch.cloud.google.com/grounding-api-redirect/` URLs.
5. **Phase 5 — Pre-PR Manuscript & OKF Gate:** Run `python scripts/five_rule_check.py <book-dir> --online-retraction-check` and `python scripts/audit_manuscript.py <book-dir> --strict` before any commit.

## 3. Narrative & Literary Rigor Directives
All drafted and edited chapters must adhere strictly to the six core directives:
- **Directive I (Concentric Movement Architecture):** 4 to 5 thematic movements per chapter anchored by a unifying conceptual narrative, concrete sensory opening/closing scenes, and causal handoffs between sections.
- **Directive II (3-Tier Causal Resolution):** Replace repetitive defensive disclaimers with positive explanatory insights:
  - *Tier 1:* Population average trajectory (public health/policy signal).
  - *Tier 2:* Individual trajectory (conditional biological/system mechanisms).
  - *Tier 3:* Actionable operator/parental control and judgment.
- **Directive III ("Then vs. Now" Landmark Set-Pieces):** One 300–500 word narrative set-piece examining a foundational experiment across 4 beats: The Original Quest, The Historical Orthodoxy, The Replication & Revision, and The Modern Consensus.
- **Directive IV (Progressive Lens Escalation):** Deduplicate recurrent empirical anchors across chapters: first appearance covers study design and biological mechanism; second appearance shifts to ecological/structural constraints; subsequent appearances focus strictly on scalability, attenuation, or persistence.
- **Directive V (Balanced Evidentiary Density):** Minimum 12–15 OKF v0.2 Evidence Cards per volume with locked primary DOIs and zero retractions across technical, organizational, and philosophical lenses alike.
- **Directive VI (Dual-Representation Oral TTS Decoupling):** Maintain dual representation (`display_html` preserving tables/symbols for visual print vs. `spoken_text` converting symbols to spoken prose for zero-drift Gemini TTS).

## 4. Prose Calibration & Forbidden Phrases
- Claim verbs must match the OKF card certainty grade: *High* → **shows**; *Moderate* → **suggests**; *Low* → **is associated with**.
- Zero unquoted forbidden phrases (`style/forbidden-phrases.md`): avoid cliché transitional filler ("delve", "testament", "crucial role", "tapestry", "game changer", "vital", "beacon").
