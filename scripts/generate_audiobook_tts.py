#!/usr/bin/env python3
"""Gemini TTS / Audiobook Synthesis Pipeline for Multi-Series Editorial Monorepo.

Transforms book chapters into clean spoken transcripts (stripping YAML frontmatter,
footnotes, Sources, and Notes), segments into semantic blocks, packs whole blocks
into TTS chunks without splitting, estimates speaking duration (--dry-run),
synthesizes 24kHz WAV audio files via Gemini 2.5 TTS, encodes MP3s, and outputs
zero-drift ground-truth audio timing sidecars (*.timings.json).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

from audio_sync_utils import (
    BYTES_PER_SECOND,
    SAMPLE_RATE,
    WPM_SPEAKING_RATE,
    build_timings_manifest,
    extract_semantic_blocks,
    pack_semantic_blocks,
    save_timings_manifest,
)
from merge_book_chapters import iter_chapter_files, repo_root, resolve_book_path


FALLBACK_TTS_MODELS = [
    "gemini-2.5-pro-preview-tts",
    "gemini-3.8-flash-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-3.8-flash-lite-tts",
    "gemini-2.5-flash-preview-tts",
]


def synthesize_chunk_pcm(text: str, voice: str, model: str, api_key: str, max_retries: int = 5) -> bytes:
    models_to_try = [model] + [m for m in FALLBACK_TTS_MODELS if m != model]
    last_err = None

    for current_model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": text
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice,
                        }
                    }
                },
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates") or []
                if not candidates:
                    raise RuntimeError("No candidates returned from Gemini TTS API.")
                parts = (candidates[0].get("content") or {}).get("parts") or []
                for p in parts:
                    inline = p.get("inlineData") or {}
                    if inline.get("data"):
                        return base64.b64decode(inline["data"])
                raise RuntimeError("No inlineData audio returned in Gemini response.")
            except urllib.error.HTTPError as e:
                last_err = e
                body_msg = ""
                try:
                    err_json = json.loads(e.read().decode("utf-8"))
                    body_msg = (err_json.get("error") or {}).get("message", "")
                except Exception:
                    pass
                if "spending cap" in body_msg.lower():
                    print(f"\n[ALERT] Monthly spending cap reached on Gemini API: {body_msg}", file=sys.stderr)
                    raise
                if e.code in [429, 500, 503] and attempt < max_retries - 1:
                    wait_s = max(3.0, float(2 ** (attempt + 1)))
                    print(f"    [{current_model}] HTTP {e.code}. Backing off {wait_s:.1f}s before retry ({attempt+1}/{max_retries})...")
                    time.sleep(wait_s)
                    continue
                elif e.code in [429, 500, 503] and current_model != models_to_try[-1]:
                    print(f"    [{current_model}] Quota reached. Falling back to alternative model...")
                    break
                raise

    if last_err:
        raise last_err
    raise RuntimeError("TTS synthesis failed across all fallback models.")


def write_wav(out_path: Path, pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit linear PCM
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def load_dotenv(root: Path) -> None:
    env_path = root / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Gemini TTS audiobook generator with zero-drift timing sidecars.")
    parser.add_argument("book", type=Path, help="Book directory (e.g. series/architectures-of-memory/book-01-vanishing-signal or series/parenthood-atlas)")
    parser.add_argument("--chapter", default=None, help="Filter to a specific chapter prefix (e.g. '01' or '07')")
    parser.add_argument("--voice", default="Kore", help="Gemini prebuilt voice name (default: Kore)")
    parser.add_argument("--model", default="gemini-2.5-flash-preview-tts", help="Gemini TTS model")
    parser.add_argument("--max-chars", type=int, default=3500, help="Max characters per chunk (when using --batch-chunks)")
    parser.add_argument("--batch-chunks", action="store_true", help="Group blocks into 3500-char chunks instead of per-paragraph chunks")
    parser.add_argument("--dry-run", action="store_true", help="Estimate duration, blocks & chunk counts without calling API")
    parser.add_argument("--encode-mp3-only", action="store_true", help="Encode existing WAVs in audiobook/ to MP3 without calling Gemini")
    parser.add_argument("--skip-existing", action="store_true", help="Skip chapters that already have complete WAV and timings JSON")
    args = parser.parse_args()

    root = repo_root()
    load_dotenv(root)
    book_path = resolve_book_path(root, args.book)
    chapters_dir = book_path / "chapters"
    out_dir = book_path / "audiobook"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.encode_mp3_only:
        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            print("error: ffmpeg not found in PATH.", file=sys.stderr)
            sys.exit(1)
        wav_files = sorted(out_dir.glob("*.wav"))
        if not wav_files:
            print("no WAV files found in audiobook/ to encode.", file=sys.stderr)
            sys.exit(0)
        for w in wav_files:
            mp3 = out_dir / f"{w.stem}.mp3"
            print(f"Encoding {w.name} -> {mp3.name}...")
            subprocess.run([ffmpeg_bin, "-y", "-i", str(w), "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3)], check=True)
        # Refresh player
        render_script = root / "scripts" / "render_audiobook_player.py"
        if render_script.exists():
            subprocess.run([sys.executable, str(render_script), str(book_path)])
        return

    if not chapters_dir.is_dir():
        print(f"error: chapters directory not found: {chapters_dir}", file=sys.stderr)
        sys.exit(1)

    md_files = iter_chapter_files(chapters_dir)
    if args.chapter:
        prefix = args.chapter.zfill(2)
        md_files = [f for f in md_files if f.name.startswith(prefix)]

    if not md_files:
        print("error: no matching chapter files found.", file=sys.stderr)
        sys.exit(1)

    total_words = 0
    total_blocks = 0
    total_chunks = 0
    rows: list[tuple[str, int, int, int, float]] = []

    per_paragraph = not args.batch_chunks

    for f in md_files:
        content = f.read_text(encoding="utf-8")
        blocks = extract_semantic_blocks(content)
        chunks = pack_semantic_blocks(blocks, max_chars=args.max_chars, per_paragraph=per_paragraph)
        words = sum(b["words"] for b in blocks)
        minutes = words / WPM_SPEAKING_RATE
        total_words += words
        total_blocks += len(blocks)
        total_chunks += len(chunks)
        rows.append((f.name, words, len(blocks), len(chunks), minutes))

    mode_str = "Single-Paragraph Exact Timestamps" if per_paragraph else f"Batched Chunks (≤ {args.max_chars} chars)"
    print(f"# Audiobook TTS Plan — {book_path.name} (Voice: {args.voice}, Mode: {mode_str})")
    print(f"{'Chapter':<38} {'Words':>7} {'Blocks':>7} {'Chunks':>7} {'Est. Min':>9}")
    print("-" * 73)
    for name, words, n_blocks, n_chunks, mins in rows:
        print(f"{name:<38} {words:>7,d} {n_blocks:>7,d} {n_chunks:>7,d} {mins:>8.1f}m")
    print("-" * 73)
    total_min = total_words / WPM_SPEAKING_RATE
    print(f"{'TOTAL':<38} {total_words:>7,d} {total_blocks:>7,d} {total_chunks:>7,d} {total_min:>8.1f}m ({total_min / 60:.2f} hrs)")

    if args.dry_run:
        return

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("\nerror: set GEMINI_API_KEY in environment to synthesize audio (or use --dry-run).", file=sys.stderr)
        sys.exit(1)

    cache_dir = root / ".cache" / "tts_pcm"
    cache_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_bin = shutil.which("ffmpeg")
    for f in md_files:
        wav_path = out_dir / f"{f.stem}.wav"
        timings_path = out_dir / f"{f.stem}.timings.json"
        mp3_path = out_dir / f"{f.stem}.mp3"
        if args.skip_existing and wav_path.exists() and timings_path.exists():
            if not ffmpeg_bin or mp3_path.exists():
                print(f"Skipping already-synthesized chapter: {f.name}")
                continue
        content = f.read_text(encoding="utf-8")
        blocks = extract_semantic_blocks(content)
        chunks = pack_semantic_blocks(blocks, max_chars=args.max_chars, per_paragraph=per_paragraph)
        pcm_all = bytearray()
        chunk_durations_sec: list[float] = []
        chunk_pcm_bytes: list[int] = []

        for idx, chunk in enumerate(chunks, 1):
            block = chunk["blocks"][0] if chunk["blocks"] else None
            tag = block["tag"] if block else "p"
            preview = chunk["spoken_text"][:50].replace("\n", " ")
            spoken_text = chunk["spoken_text"]

            cache_key = hashlib.sha256(f"{args.voice}:{args.model}:{spoken_text}".encode("utf-8")).hexdigest()
            cache_file = cache_dir / f"{cache_key}.pcm"

            if cache_file.exists():
                print(f"Loaded cached {f.stem} [{idx}/{len(chunks)}] <{tag}> ({chunk['total_words']}w): {repr(preview)}...", flush=True)
                pcm = cache_file.read_bytes()
            else:
                print(f"Synthesizing {f.stem} [{idx}/{len(chunks)}] <{tag}> ({chunk['total_words']}w): {repr(preview)}...", flush=True)
                pcm = synthesize_chunk_pcm(spoken_text, voice=args.voice, model=args.model, api_key=api_key)
                cache_file.write_bytes(pcm)
                time.sleep(1.0)

            # Insert calibrated natural breath pause after block
            if tag in ["h1", "h2", "h3"]:
                pause_sec = 0.45
            elif tag == "li":
                pause_sec = 0.20
            elif tag == "tr":
                pause_sec = 0.35
            else:
                pause_sec = 0.30

            pause_bytes = b"\x00" * int(SAMPLE_RATE * 2 * pause_sec)
            block_pcm = pcm + pause_bytes
            dur = len(block_pcm) / BYTES_PER_SECOND

            chunk_durations_sec.append(dur)
            chunk_pcm_bytes.append(len(block_pcm))
            pcm_all.extend(block_pcm)
            print(f"  -> {dur:.2f}s total (audio: {len(pcm)/BYTES_PER_SECOND:.2f}s + {pause_sec:.2f}s breath)")

        wav_path = out_dir / f"{f.stem}.wav"
        write_wav(wav_path, bytes(pcm_all))
        print(f"Wrote master WAV: {wav_path}")

        # Build and save zero-drift timings sidecar JSON
        manifest = build_timings_manifest(f.stem, chunks, chunk_durations_sec, chunk_pcm_bytes)
        timings_path = out_dir / f"{f.stem}.timings.json"
        save_timings_manifest(manifest, timings_path)
        print(f"Wrote zero-drift ground-truth timings sidecar: {timings_path}")

        if ffmpeg_bin:
            mp3_path = out_dir / f"{f.stem}.mp3"
            res = subprocess.run(
                [ffmpeg_bin, "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3_path)],
                capture_output=True,
            )
            if res.returncode == 0:
                print(f"Wrote web-streamable MP3: {mp3_path}")

        # Update player after each completed chapter
        render_script = root / "scripts" / "render_audiobook_player.py"
        if render_script.exists():
            subprocess.run([sys.executable, str(render_script), str(book_path)], capture_output=True)

    # Re-render audio player
    render_script = root / "scripts" / "render_audiobook_player.py"
    if render_script.exists():
        subprocess.run([sys.executable, str(render_script), str(book_path)])


if __name__ == "__main__":
    main()
