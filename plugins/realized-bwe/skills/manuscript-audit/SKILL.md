---
name: manuscript-audit
description: >-
  Audits a book or series directory for series-bible compliance, metaphor collisions,
  footnote integrity, forbidden phrases, OKF v0.2 evidence cards, character continuity,
  fact-check debt, and optional long-context Gemini review. Use when the user asks to
  audit a manuscript, check continuity across chapters, or lint footnotes/metaphors.
---

# Manuscript, Continuity & OKF Audit

## Steps

1. **Deterministic Structural & OKF Audit:**
   Run [`scripts/audit_manuscript.py`](../../../scripts/audit_manuscript.py) on the target book or series folder:
   ```powershell
   python scripts/audit_manuscript.py series/architectures-of-memory/book-01-vanishing-signal --strict
   python scripts/audit_manuscript.py series/parenthood-atlas --strict
   ```
2. **OKF v0.2 Five-Rule Gate (with Live Crossref/OpenAlex Retraction Check):**
   ```powershell
   python scripts/five_rule_check.py series/architectures-of-memory/book-01-vanishing-signal --online-retraction-check
   python scripts/five_rule_check.py series/parenthood-atlas --summary-only
   ```
3. **Long-Context Gemini Editorial Review (Optional):**
   When `GEMINI_API_KEY` is set, run with `--gemini` to evaluate voice, three-lens rhythm, and philosophical/scientific depth across the full book in a single 1M-token context window:
   ```powershell
   python scripts/audit_manuscript.py series/architectures-of-memory/book-01-vanishing-signal --gemini
   ```
