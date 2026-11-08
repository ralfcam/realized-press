---
name: phrasal-polish
description: >-
  Executes SotA LLM Frozen-Skeleton Phrasal Sculpting across book chapters using
  style/phrasal-poetics.yml, bwe/style_sculptor.py, and scripts/audit_manuscript.py --poetics.
  Use when the user asks to elevate literary style, sculpt flat or copula-heavy prose,
  fix sentence cadence monotony, split wall-of-text paragraphs, or run phrasal poetics audits.
---

# SotA LLM Frozen-Skeleton Phrasal Sculpting (`ARC-104`)

## Core Architecture: Decoupling Epistemic Skeleton from Phrasal Surface
In Realized Press, literary style elevation must **never** alter scientific certainty grades, quantitative effect sizes, or citation bindings. All phrasal polishing follows the **3-Stage Frozen-Skeleton Pipeline** (`bwe/style_sculptor.py`):

1. **Stage 1 — Extract & Freeze Epistemic Skeleton (`extract_epistemic_skeleton`):**
   - Lock all inline footnote keys (`[^ch01-...]`), bold grade-calibrated claim verbs (`**shows**`, `**suggests**`, `**is associated with**`), quantitative anchors (`N = ...`, `RR = ...`, percentages, dates), and italicized first-contact terms.
2. **Stage 2 — Five Phrasal-Sculpting Operations (`build_sculptor_prompt`):**
   - **Operation A (Kinetic Verbs over Copulas):** Replace weak state-of-being verbs (`is`, `are`, `has`, `becomes`, `provides`, `serves as`) with 1–2 syllable Anglo-Saxon kinetic verbs from `style/phrasal-poetics.yml` (`anchor`, `bar`, `confiscate`, `disarm`, `filter`, `pry`, `clamp`, `hinge`, `dampen`, `flood`, `cradle`, `mirror`).
   - **Operation B (Sustained Controlling Metaphor):** Derive paragraph verbs and concrete nouns from the chapter's OKF v0.3 `canonical_metaphors` without mixing conflicting metaphors in the same movement.
   - **Operation C (Asymmetric Cadence & Aphoristic Hinge):** Engineer sentence-length standard deviation $\sigma \ge 3.0\text{w}$ by pairing a 22–28 word periodic setup sentence with a crisp 5–9 word declarative hinge sentence separated by a period (`.`). Avoid joining independent clauses with semicolons (`;`), which inflate Flesch-Kincaid grade.
   - **Operation D (Zero Nominalization Clusters or Participial Tail-Drags):** Eliminate clauses with $>2$ abstract `-tion/-ment/-ity` nouns and strip formulaic LLM participial tail clauses (`, highlighting...`, `, underscoring...`, `, ensuring...`).
   - **Operation E (Micro-QA & Pagination Conservation):** Keep every paragraph $\le 135$ words and $\le 6$ sentences, every sentence $\le 35$ words (EN) / $\le 38$ words (ES), and local paragraph FK Grade $\le 12.0$ while preserving exact KDP 6"×9" chapter page spans.
3. **Stage 3 — Mechanical Verification Gate (`verify_sculpted_candidate`):**
   - Verify 100% preservation of frozen footnotes, epistemic verbs, and quantitative tokens alongside zero hard errors or warnings in `audit_manuscript.py --bestseller-strict --graph-strict --micro-strict --poetics`.

## CLI Workflow

1. **Run Book-Wide Phrasal Poetics & Micro-QA Audit:**
   ```powershell
   python scripts/audit_manuscript.py series/parenthood-atlas --bestseller-strict --graph-strict --micro-strict --poetics
   ```
2. **Generate a Chapter Frozen-Skeleton Sculpt Pack:**
   ```powershell
   python -m bwe.cli sculpt --series parenthood-atlas --chapter 04-regulatory-relationship --top-k 5 --dry-run
   ```
3. **Verify Print Pagination & Apparatus Integrity After Sculpting:**
   ```powershell
   python scripts/merge_book_chapters.py series/parenthood-atlas
   python scripts/render_publishing_pdfs.py series/parenthood-atlas --format a4
   python scripts/render_publishing_pdfs.py series/parenthood-atlas --format kdp-6x9 --epub
   python scripts/audit_pdf_layout.py series/parenthood-atlas
   ```

## Two-Pass Localization & Posterior Native Phrasal-Sculpting (`ARC-105`)

Every localized edition (`i18n/es`, and `i18n/fr` when unpaused) requires a mandatory **Pass 2 Posterior Phrasal-Sculpting Pass** after **Pass 1 Epistemic & Regional Transfer**:

1. **Frozen Multilingual Skeleton:** Preserve 100% of canonical `[^chXX-...]` keys, target-market regional footnotes (`[^chXX-es-...]`), grade-calibrated bold claim verbs (`**muestra/demuestra**`, `**sugiere/indica**`, `**se asocia con**`), quantitative anchors, and `i18n/<lang>/style/lexicon.yaml` search-intent weaves.
2. **Five Target-Language Sculpting Operations (`--lang es`):**
   - Replace `ser/estar/haber/tener` copula inflation and passive calques with active pronominal/kinetic verbs from `i18n/es/style/phrasal-poetics.yml` (`intercepta`, `desactiva`, `blinda`, `sella`, `amortigua`, `encarrila`, `desborda`).
   - Prune Romance `de + sustantivo` genitive chains and `-ción/-miento/-dad` nominalization clusters (`0` clusters).
   - Purge trailing gerund tail-drags (`gerundio de posterioridad`: `, destacando...`, `, subrayando...`, `, facilitando...`) and cap `"no es X, sino Y"` pivots at $\le 3$ per chapter.
   - Engineer native Castilian clausal counterpoint ($\sigma \ge 3.0\text{w}$, `0` cadence flags).
   - De-wall all expanded translated paragraphs to $\le 135$ words, $\le 6$ sentences, and local Szigriszt $\ge 42.0$ (chapter Szigriszt $\ge 52.0$, avg sentence $\le 20.5\text{w}$, `0` sentences $>38\text{w}$, `Poetics Score >= 95.0`).
3. **Localized Audit Command:**
   ```powershell
   python scripts/audit_manuscript.py series/parenthood-atlas/i18n/es --bestseller-strict --graph-strict --micro-strict --poetics --lang es
   ```
