#!/usr/bin/env python3
"""Audiobook TTS synthesis daemon for Parenthood: The Atlas (English & Spanish).

Executes full 15-chapter Gemini TTS synthesis for:
1. English Gold-Master edition (series/parenthood-atlas/)
2. Spanish Gold-Master edition (series/parenthood-atlas/i18n/es/)
Generates master WAVs, streaming MP3s, block-level timings sidecars (*.timings.json),
and compiles synchronized HTML5 players.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_command(cmd: list[str], desc: str) -> None:
    print(f"\n{'='*70}\n[DAEMON] Starting {desc}\nCMD: {' '.join(cmd)}\n{'='*70}\n", flush=True)
    start_t = time.time()
    res = subprocess.run(cmd, cwd=ROOT)
    elapsed = time.time() - start_t
    if res.returncode != 0:
        print(f"[DAEMON:ERROR] {desc} failed with exit code {res.returncode} after {elapsed:.1f}s", file=sys.stderr, flush=True)
        sys.exit(res.returncode)
    print(f"[DAEMON:PASS] {desc} completed in {elapsed:.1f}s\n", flush=True)


def main() -> None:
    print("=== Parenthood: The Atlas Dual-Language Audiobook TTS Daemon Starting ===", flush=True)

    # 1. English Edition (series/parenthood-atlas)
    run_command(
        [sys.executable, "scripts/generate_audiobook_tts.py", "series/parenthood-atlas", "--voice", "Kore", "--skip-existing"],
        "English Audiobook TTS Synthesis (series/parenthood-atlas)",
    )
    run_command(
        [sys.executable, "scripts/render_audiobook_player.py", "series/parenthood-atlas"],
        "English Audiobook Player Compilation (series/parenthood-atlas/audiobook/index.html)",
    )

    # 2. Spanish Edition (series/parenthood-atlas/i18n/es)
    run_command(
        [sys.executable, "scripts/generate_audiobook_tts.py", "series/parenthood-atlas/i18n/es", "--voice", "Kore", "--skip-existing"],
        "Spanish Audiobook TTS Synthesis (series/parenthood-atlas/i18n/es)",
    )
    run_command(
        [sys.executable, "scripts/render_audiobook_player.py", "series/parenthood-atlas/i18n/es"],
        "Spanish Audiobook Player Compilation (series/parenthood-atlas/i18n/es/audiobook/index.html)",
    )

    print("\n[DAEMON:COMPLETE] Both English and Spanish audiobooks and synchronized players generated successfully!", flush=True)


if __name__ == "__main__":
    main()
