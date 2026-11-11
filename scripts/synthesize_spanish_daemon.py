#!/usr/bin/env python3
"""Spanish Audiobook TTS synthesis daemon for El atlas de la crianza.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_command(cmd: list[str], desc: str) -> None:
    print(f"\n{'='*70}\n[SPANISH DAEMON] Starting {desc}\nCMD: {' '.join(cmd)}\n{'='*70}\n", flush=True)
    start_t = time.time()
    res = subprocess.run(cmd, cwd=ROOT)
    elapsed = time.time() - start_t
    if res.returncode != 0:
        print(f"[SPANISH DAEMON:ERROR] {desc} failed with exit code {res.returncode} after {elapsed:.1f}s", file=sys.stderr, flush=True)
        sys.exit(res.returncode)
    print(f"[SPANISH DAEMON:PASS] {desc} completed in {elapsed:.1f}s\n", flush=True)


def main() -> None:
    print("=== Spanish Audiobook TTS Synthesis Starting ===", flush=True)
    run_command(
        [sys.executable, "scripts/generate_audiobook_tts.py", "series/parenthood-atlas/i18n/es", "--voice", "Kore", "--model", "gemini-3.1-flash-tts-preview", "--skip-existing"],
        "Spanish Audiobook TTS Synthesis (series/parenthood-atlas/i18n/es)",
    )
    run_command(
        [sys.executable, "scripts/render_audiobook_player.py", "series/parenthood-atlas/i18n/es"],
        "Spanish Audiobook Player Compilation (series/parenthood-atlas/i18n/es/audiobook/index.html)",
    )
    run_command(
        [sys.executable, "scripts/render_audiobook_player.py", "--imprint"],
        "Imprint Portal Sync (dist/site/ and docs/)",
    )
    print("\n[SPANISH DAEMON:COMPLETE] Spanish audiobook and synchronized player generated successfully!", flush=True)


if __name__ == "__main__":
    main()
