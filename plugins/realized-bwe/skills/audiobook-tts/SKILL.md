---
name: audiobook-tts
description: >-
  Compiles TTS-ready chapter transcripts and synthesizes audiobook audio files using
  Gemini Audio / TTS across Architectures of Memory and Parenthood: The Atlas. Use when
  the user asks to generate audiobook audio, estimate audiobook duration, or run
  text-to-speech on book chapters.
---

# Audiobook TTS Pipeline (Multi-Series)

## Steps

1. **Merge Audiobook Transcript:**
   ```powershell
   python scripts/merge_book_chapters.py series/architectures-of-memory/book-01-vanishing-signal --audiobook --prefix vanishing-signal
   python scripts/merge_book_chapters.py series/parenthood-atlas --audiobook --prefix parenthood-atlas
   ```
2. **Dry-Run & Duration Estimate (No API Call):**
   Inspect word counts, TTS chunks, and estimated speaking duration per chapter:
   ```powershell
   python scripts/generate_audiobook_tts.py series/architectures-of-memory/book-01-vanishing-signal --dry-run
   python scripts/generate_audiobook_tts.py series/parenthood-atlas --dry-run
   ```
3. **Synthesize Chapter Audio (Requires `GEMINI_API_KEY`):**
   Synthesize `.wav` files for a specific chapter or the full book into `<book-dir>/audiobook/`:
   ```powershell
   python scripts/generate_audiobook_tts.py series/architectures-of-memory/book-01-vanishing-signal --chapter 01 --voice Kore
   ```
