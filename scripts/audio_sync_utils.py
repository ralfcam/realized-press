#!/usr/bin/env python3
"""Shared Semantic Audio-Text Synchronization Utilities for Realized Press BWE.

Implements Approach 2:
1. Semantic Block Segmentation from Chapter Markdown (H1, H2, H3, P, LI, Table, Blockquote).
2. HTML-Aware Greedy Block Packing into TTS Chunks (blocks never cut across chunks).
3. PCM Buffer Duration Extraction and Absolute Second Timestamp Calibration.
4. Timings Sidecar Serialization (*.timings.json).
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import bs4
import markdown
from merge_book_chapters import strip_yaml_frontmatter, transform_audiobook

WPM_SPEAKING_RATE = 150
SAMPLE_RATE = 24000  # 24kHz 16-bit linear mono PCM
BYTES_PER_SECOND = SAMPLE_RATE * 2  # 48,000 bytes/sec

HEADING_PAUSE_WORDS = {
    "h1": 3,
    "h2": 2,
    "h3": 2,
    "li": 1,
    "tr": 2,
}


def clean_spoken_text(text: str) -> str:
    """Clean markdown formatting remnants, HTML tags, and mathematical symbols for natural vocal cadence."""
    # Strip HTML tags (e.g. <aside>, </aside>, <div>) so raw tags are never vocalized
    t = re.sub(r"</?[a-zA-Z][^>]*>", " ", text)
    # Strip markdown bold, italics, inline code, and footnotes
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"\[\^[^^\]]+\]", "", t)

    # Normalize mathematical symbols and causal arrows for natural spoken narration
    t = t.replace("→", " leads to ").replace("->", " leads to ")
    t = t.replace("←", " from ").replace("<-", " from ")
    t = t.replace("≈", " approximately ")
    t = t.replace("≤", " less than or equal to ")
    t = t.replace("≥", " greater than or equal to ")
    t = t.replace("≠", " not equal to ")
    t = t.replace("×", " times ")
    t = t.replace(r"\approx", " approximately ")
    t = t.replace(r"\to", " leads to ")
    t = t.replace(r"\rightarrow", " leads to ")

    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_semantic_blocks(md_content: str) -> list[dict[str, Any]]:
    """Extract ordered sequence of discrete semantic blocks from chapter markdown."""
    spoken_body = transform_audiobook(md_content)
    html_raw = markdown.markdown(spoken_body, extensions=["extra", "smarty", "sane_lists"])
    soup = bs4.BeautifulSoup(html_raw, "html.parser")

    # Clean footnote anchors inside the spoken AST
    for sup in soup.find_all(lambda t: t.name == "sup" and (t.get("id", "").startswith("fnref") or t.find("a", class_="footnote-ref"))):
        sup.decompose()
    for fn_div in soup.find_all("div", class_="footnote"):
        fn_div.decompose()

    blocks: list[dict[str, Any]] = []
    idx = 0

    for el in soup.children:
        if not isinstance(el, bs4.Tag):
            continue

        if el.name in ["h1", "h2", "h3", "p"]:
            txt = clean_spoken_text(el.get_text())
            if not txt:
                continue
            # Ensure title and headings have a closing period for vocal cadence
            spoken = txt if txt.endswith((".", "!", "?", ":", ";", "—")) else f"{txt}."
            words = len(txt.split())
            bonus = HEADING_PAUSE_WORDS.get(el.name, 0)
            blocks.append({
                "id": f"b-{idx:03d}",
                "tag": el.name,
                "clean_text": txt,
                "spoken_text": spoken,
                "words": words,
                "weight": max(1, words + bonus),
            })
            idx += 1

        elif el.name in ["ul", "ol"]:
            for li in el.find_all("li", recursive=False):
                txt = clean_spoken_text(li.get_text())
                if not txt:
                    continue
                spoken = txt if txt.endswith((".", "!", "?", ":", ";", "—")) else f"{txt}."
                words = len(txt.split())
                bonus = HEADING_PAUSE_WORDS.get("li", 1)
                blocks.append({
                    "id": f"b-{idx:03d}",
                    "tag": "li",
                    "clean_text": txt,
                    "spoken_text": spoken,
                    "words": words,
                    "weight": max(1, words + bonus),
                })
                idx += 1

        elif el.name == "table":
            headers = [clean_spoken_text(th.get_text()) for th in el.find_all("th")]
            row_sentences = []
            for tr in el.find_all("tr"):
                cells = [clean_spoken_text(td.get_text()) for td in tr.find_all("td")]
                if cells:
                    row_parts = []
                    for h, c in zip(headers, cells):
                        if h and c:
                            row_parts.append(f"{h}: {c}")
                        elif c:
                            row_parts.append(c)
                    if row_parts:
                        row_sentences.append(", ".join(row_parts))
            if row_sentences:
                spoken = ". ".join(row_sentences) + "."
                words = len(spoken.split())
                blocks.append({
                    "id": f"b-{idx:03d}",
                    "tag": "table",
                    "clean_text": spoken,
                    "spoken_text": spoken,
                    "words": words,
                    "weight": max(1, words),
                })
                idx += 1

        elif el.name == "blockquote":
            for p_tag in el.find_all("p"):
                txt = clean_spoken_text(p_tag.get_text())
                if not txt:
                    continue
                spoken = txt if txt.endswith((".", "!", "?", ":", ";", "—")) else f"{txt}."
                words = len(txt.split())
                blocks.append({
                    "id": f"b-{idx:03d}",
                    "tag": "blockquote",
                    "clean_text": txt,
                    "spoken_text": spoken,
                    "words": words,
                    "weight": max(1, words),
                })
                idx += 1

    return blocks


def pack_semantic_blocks(
    blocks: list[dict[str, Any]],
    max_chars: int = 3500,
    per_paragraph: bool = False,
) -> list[dict[str, Any]]:
    """Pack semantic blocks into TTS chunks.

    If per_paragraph is True, each individual semantic block forms its own chunk,
    yielding 100% exact ground-truth audio timestamps for every paragraph without estimation.
    Otherwise, blocks are greedily packed up to max_chars without splitting across blocks.
    """
    if per_paragraph:
        chunks: list[dict[str, Any]] = []
        for idx, b in enumerate(blocks, 1):
            chunks.append({
                "chunk_id": idx,
                "blocks": [b],
                "spoken_text": b["spoken_text"],
                "total_chars": len(b["spoken_text"]),
                "total_words": b["words"],
                "total_weight": b["weight"],
            })
        return chunks

    chunks: list[dict[str, Any]] = []
    curr_blocks: list[dict[str, Any]] = []
    curr_len = 0
    chunk_idx = 1

    for b in blocks:
        spoken = b["spoken_text"]
        b_len = len(spoken)
        # Check if adding this block exceeds limit (and current chunk is non-empty)
        if curr_len + b_len + 2 > max_chars and curr_blocks:
            chunks.append({
                "chunk_id": chunk_idx,
                "blocks": curr_blocks,
                "spoken_text": "\n\n".join(bk["spoken_text"] for bk in curr_blocks),
                "total_chars": sum(len(bk["spoken_text"]) for bk in curr_blocks),
                "total_words": sum(bk["words"] for bk in curr_blocks),
                "total_weight": sum(bk["weight"] for bk in curr_blocks),
            })
            chunk_idx += 1
            curr_blocks = [b]
            curr_len = b_len
        else:
            curr_blocks.append(b)
            curr_len += b_len + 2

    if curr_blocks:
        chunks.append({
            "chunk_id": chunk_idx,
            "blocks": curr_blocks,
            "spoken_text": "\n\n".join(bk["spoken_text"] for bk in curr_blocks),
            "total_chars": sum(len(bk["spoken_text"]) for bk in curr_blocks),
            "total_words": sum(bk["words"] for bk in curr_blocks),
            "total_weight": sum(bk["weight"] for bk in curr_blocks),
        })

    return chunks


def build_timings_manifest(
    chapter_stem: str,
    chunks: list[dict[str, Any]],
    chunk_durations_sec: list[float] | None = None,
    chunk_pcm_bytes: list[int] | None = None,
) -> dict[str, Any]:
    """Calculate absolute block timings from exact chunk durations and emit timings manifest."""
    manifest_chunks = []
    manifest_blocks = []
    current_time = 0.0

    for idx, chunk in enumerate(chunks):
        c_id = chunk["chunk_id"]
        if chunk_durations_sec and idx < len(chunk_durations_sec):
            dur = chunk_durations_sec[idx]
        else:
            # Fallback estimation for dry run
            dur = (chunk["total_words"] / WPM_SPEAKING_RATE) * 60.0

        pcm_len = chunk_pcm_bytes[idx] if chunk_pcm_bytes and idx < len(chunk_pcm_bytes) else int(dur * BYTES_PER_SECOND)

        chunk_start = current_time
        chunk_end = current_time + dur
        current_time = chunk_end

        chunk_weight = chunk["total_weight"] or 1
        block_cursor = chunk_start

        c_blocks = chunk["blocks"]
        block_ids = [b["id"] for b in c_blocks]

        manifest_chunks.append({
            "chunk_id": c_id,
            "start_sec": round(chunk_start, 3),
            "end_sec": round(chunk_end, 3),
            "duration_sec": round(dur, 3),
            "pcm_bytes": pcm_len,
            "block_range": [block_ids[0], block_ids[-1]] if block_ids else [],
        })

        for b in c_blocks:
            b_dur = dur * (b["weight"] / chunk_weight)
            b_start = block_cursor
            b_end = block_cursor + b_dur
            block_cursor = b_end

            manifest_blocks.append({
                "id": b["id"],
                "tag": b["tag"],
                "chunk_id": c_id,
                "start_sec": round(b_start, 3),
                "end_sec": round(b_end, 3),
                "words": b["words"],
                "weight": b["weight"],
                "text": b["clean_text"],
            })

    total_duration = round(current_time, 3)
    # Calibrate relative ratios for backwards compatibility with ratio-based players
    for mb in manifest_blocks:
        mb["start_ratio"] = round(mb["start_sec"] / total_duration, 4) if total_duration > 0 else 0.0
        mb["end_ratio"] = round(mb["end_sec"] / total_duration, 4) if total_duration > 0 else 0.0

    return {
        "chapter": chapter_stem,
        "total_duration_sec": total_duration,
        "sample_rate": SAMPLE_RATE,
        "bytes_per_second": BYTES_PER_SECOND,
        "chunks": manifest_chunks,
        "blocks": manifest_blocks,
    }


def save_timings_manifest(manifest: dict[str, Any], out_path: Path) -> None:
    """Save timings manifest to JSON sidecar file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def load_timings_manifest(timings_path: Path) -> dict[str, Any] | None:
    """Load timings manifest if exists, else None."""
    if timings_path.is_file():
        try:
            return json.loads(timings_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None
