#!/usr/bin/env python3
"""Audiobook Web Player & Marketing Portal Generator for Realized Press Imprint.

Centralizes the standalone HTML5 audiobook web player across all series and volumes,
serving as the foundational architecture for the owned marketing and serial-membership site.
Features deep mobile-first UX/UI (safe-area insets, 44px+ touch targets, native MediaSession API,
compact segmented mobile book switcher, and typography-calibrated synchronized reading).

Modes:
  1. Single-Book Mode:
     python scripts/render_audiobook_player.py series/parenthood-atlas
  2. Centralized Imprint Portal Mode:
     python scripts/render_audiobook_player.py --imprint [--output site]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

import markdown
import bs4
from audio_sync_utils import HEADING_PAUSE_WORDS, load_timings_manifest
from merge_book_chapters import iter_chapter_files, repo_root, resolve_book_path, strip_yaml_frontmatter, transform_audiobook

WPM_SPEAKING_RATE = 150
DEFAULT_GITHUB_REPO = "ralfcam/realized-press"


def extract_chapter_title(md_path: Path) -> str:
    content = md_path.read_text(encoding="utf-8")
    m = re.search(r'^title:\s*["\']?([^"\'\n]+)["\']?', content, flags=re.MULTILINE)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    if m2:
        return m2.group(1).strip()
    return md_path.stem.replace("-", " ").title()


def format_time_sec(sec: float) -> str:
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}:{s:02d}"


def extract_clean_text(md_path: Path, timings_path: Path | None = None) -> str:
    content = md_path.read_text(encoding="utf-8")
    body = strip_yaml_frontmatter(content)
    # Filter out non-prose internal domain markers
    lines = []
    for line in body.splitlines(keepends=True):
        if line.lstrip().startswith("> **Domain") or line.lstrip().startswith("*Sources:"):
            continue
        lines.append(line)
    clean_md = "".join(lines)
    # Render with full markdown parser including footnotes, tables, smart typography
    html_raw = markdown.markdown(
        clean_md,
        extensions=["extra", "smarty", "sane_lists"],
    )
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_raw, "html.parser")

    # Mark all footnote links & footnote definitions as non-spoken visual apparatus
    for sup in soup.find_all(lambda t: t.name == "sup" and (t.get("id", "").startswith("fnref") or t.find("a", class_="footnote-ref"))):
        sup["data-spoken"] = "false"
        classes = sup.get("class", []) or []
        sup["class"] = classes + ["non-spoken"]
    for fn_div in soup.find_all("div", class_="footnote"):
        fn_div["data-spoken"] = "false"
        classes = fn_div.get("class", []) or []
        fn_div["class"] = classes + ["non-spoken"]

    # Traverse document in structural order for semantic spoken elements
    elements = []
    for el in soup.children:
        if not isinstance(el, bs4.Tag):
            continue
        if el.name in ["h1", "h2", "h3", "p"]:
            elements.append(el)
        elif el.name in ["ul", "ol"]:
            for li in el.find_all("li", recursive=False):
                elements.append(li)
        elif el.name == "table":
            elements.append(el)
        elif el.name == "blockquote":
            p_children = el.find_all("p")
            if p_children:
                for p_tag in p_children:
                    elements.append(p_tag)
            else:
                elements.append(el)

    manifest = load_timings_manifest(timings_path) if timings_path else None
    if manifest and manifest.get("blocks"):
        blocks = manifest["blocks"]
        for idx, el in enumerate(elements):
            if idx < len(blocks):
                b = blocks[idx]
                el["id"] = b["id"]
                classes = el.get("class", []) or []
                el["class"] = classes + ["sync-segment"]
                el["data-start-time"] = f"{b['start_sec']:.2f}"
                el["data-end-time"] = f"{b['end_sec']:.2f}"
                el["data-start-ratio"] = f"{b['start_ratio']:.4f}"
                el["data-end-ratio"] = f"{b['end_ratio']:.4f}"
                el["data-chunk-id"] = str(b.get("chunk_id", 1))
                el["data-seg-idx"] = str(idx)
                el["title"] = f"Tap to jump audio to {format_time_sec(b['start_sec'])}"
            else:
                el["data-spoken"] = "false"
                classes = el.get("class", []) or []
                el["class"] = classes + ["non-spoken"]
    else:
        # Fallback to calibrated word-weight model
        spoken_cutoff = len(elements)
        for i, el in enumerate(elements):
            if el.name in ["h2", "h3"] and el.get_text().strip().lower() in [
                "notes", "sources", "further reading", "linked evidence cards"
            ]:
                spoken_cutoff = i
                break

        def segment_weight(el) -> int:
            base_words = len(el.get_text().split())
            if base_words == 0:
                return 0
            pause_bonus = HEADING_PAUSE_WORDS.get(el.name, 0)
            return base_words + pause_bonus

        spoken_elements = elements[:spoken_cutoff]
        total_weight = sum(segment_weight(s) for s in spoken_elements) or 1

        cum_weight = 0
        for idx, s in enumerate(elements):
            if idx < spoken_cutoff:
                w = segment_weight(s)
                start_ratio = round(cum_weight / total_weight, 4)
                cum_weight += w
                end_ratio = round(cum_weight / total_weight, 4)
                classes = s.get("class", []) or []
                s["class"] = classes + ["sync-segment"]
                s["data-start-ratio"] = str(start_ratio)
                s["data-end-ratio"] = str(end_ratio)
                s["data-seg-idx"] = str(idx)
                s["title"] = f"Tap to jump audio to ~{start_ratio*100:.1f}%"
            else:
                s["data-spoken"] = "false"
                classes = s.get("class", []) or []
                s["class"] = classes + ["non-spoken"]

    return str(soup)


def collect_book_data(book_path: Path, series_title: str, series_subtitle: str, release_tag: str, repo: str) -> dict:
    chapters_dir = book_path / "chapters"
    audio_dir = book_path / "audiobook"
    book_title = book_path.name.replace("-", " ").title()
    subtitle = series_subtitle

    # Check for series.yaml title if single-volume
    s_yaml = book_path / "series.yaml"
    if s_yaml.exists():
        import yaml
        try:
            cfg = yaml.safe_load(s_yaml.read_text(encoding="utf-8")) or {}
            book_title = cfg.get("title", book_title)
            subtitle = cfg.get("subtitle", subtitle)
        except Exception:
            pass

    # Check for book outline or README title
    outline_file = book_path / "outline.md"
    if outline_file.exists():
        content = outline_file.read_text(encoding="utf-8")
        m = re.search(r"^#\s+Book\s+\d+\s+[—–-]\s*(.+)$", content, flags=re.MULTILINE)
        if m:
            book_title = m.group(1).strip()
        m_sub = re.search(r"^\*\*Subtitle:\*\*\s*(.+)$", content, flags=re.MULTILINE)
        if m_sub:
            subtitle = m_sub.group(1).strip()

    md_files = iter_chapter_files(chapters_dir) if chapters_dir.is_dir() else []
    chapters = []
    for idx, f in enumerate(md_files, 1):
        content = f.read_text(encoding="utf-8")
        words = len(content.split())
        title = extract_chapter_title(f)
        stem = f.stem
        mp3_file = audio_dir / f"{stem}.mp3"
        wav_file = audio_dir / f"{stem}.wav"
        has_mp3 = mp3_file.exists()
        has_wav = wav_file.exists()
        mtime = int(mp3_file.stat().st_mtime) if has_mp3 else (int(wav_file.stat().st_mtime) if has_wav else 0)
        online_url = f"https://github.com/{repo}/releases/download/{release_tag}/{stem}.mp3"
        local_url = f"{stem}.mp3?v={mtime}" if has_mp3 else (f"{stem}.wav?v={mtime}" if has_wav else f"{stem}.mp3")
        timings_file = audio_dir / f"{stem}.timings.json"
        clean_html = extract_clean_text(f, timings_file)

        chapters.append({
            "num": idx,
            "stem": stem,
            "title": title,
            "words": words,
            "minutes": f"{words / WPM_SPEAKING_RATE:.1f}",
            "hasLocalMp3": has_mp3,
            "hasLocalWav": has_wav,
            "hasTimings": timings_file.exists(),
            "onlineUrl": online_url,
            "localUrl": local_url,
            "transcriptHtml": clean_html,
        })

    return {
        "id": book_path.name,
        "title": book_title,
        "subtitle": subtitle,
        "seriesTitle": series_title,
        "releaseTag": release_tag,
        "chapters": chapters,
        "hasAudio": any(c["hasLocalMp3"] or c["hasLocalWav"] for c in chapters) or (release_tag == "v1.0-rc1" and book_path.name == "parenthood-atlas"),
    }


def scan_all_imprint_books(root: Path, repo: str) -> list[dict]:
    import yaml
    catalog = []
    series_dir = root / "series"
    if not series_dir.is_dir():
        return catalog

    for s in sorted(series_dir.iterdir()):
        if not s.is_dir():
            continue
        s_yaml = s / "series.yaml"
        s_cfg = {}
        if s_yaml.exists():
            try:
                s_cfg = yaml.safe_load(s_yaml.read_text(encoding="utf-8")) or {}
            except Exception:
                pass
        series_title = s_cfg.get("title", s.name.replace("-", " ").title())
        series_subtitle = s_cfg.get("subtitle", "Autonomous Nonfiction Publishing Imprint")

        # Check multi-book vs single-book
        sub_books = [b for b in sorted(s.iterdir()) if b.is_dir() and b.name.startswith("book-")]
        if sub_books:
            for b in sub_books:
                release_tag = "aom-v1.0"
                catalog.append(collect_book_data(b, series_title, series_subtitle, release_tag, repo))
        else:
            release_tag = "v1.0-rc1" if s.name == "parenthood-atlas" else "v1.0"
            catalog.append(collect_book_data(s, series_title, series_subtitle, release_tag, repo))

    return catalog


def render_portal_html(catalog: list[dict], repo: str) -> str:
    catalog_json = json.dumps(catalog, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="theme-color" content="#070a0e">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>Realized Press — Imprint Audiobook Portal & Marketing Hub</title>
  <meta name="description" content="Official Audiobook Web Player, Serial Preprints, and Public Evidence Briefs from Realized Press imprint.">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
  <style>
    :root {{
      --bg: #0c0a09;
      --card-bg: #1c1917;
      --card-hover: #292524;
      --border: #292524;
      --border-light: #44403c;
      --gold: #f59e0b;
      --gold-light: #fbbf24;
      --gold-dim: rgba(245, 158, 11, 0.12);
      --gold-glow: rgba(245, 158, 11, 0.25);
      --text: #f5f5f4;
      --text-muted: #a8a29e;
      --accent: #38bdf8;
      --success: #34d399;
      --sidebar-w: 320px;
      --dock-h: 104px;
      --safe-bottom: env(safe-area-inset-bottom, 0px);
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      padding-bottom: calc(var(--dock-h) + var(--safe-bottom) + 24px);
    }}

    /* Top Navigation */
    .navbar {{
      background: rgba(7, 10, 14, 0.92);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 12px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 200;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
      color: #fff;
    }}
    .brand-mark {{
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, var(--gold), #9e6a03);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.1rem;
      color: #000;
      box-shadow: 0 2px 8px rgba(210, 153, 34, 0.3);
      flex-shrink: 0;
    }}
    .brand-text h1 {{
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      line-height: 1.2;
    }}
    .brand-text p {{
      font-size: 0.68rem;
      color: var(--gold);
      letter-spacing: 0.06em;
      text-transform: uppercase;
      font-weight: 700;
      line-height: 1.1;
    }}
    .nav-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .nav-badge {{
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--gold);
      background: var(--gold-dim);
      border: 1px solid rgba(210, 153, 34, 0.3);
      padding: 4px 10px;
      border-radius: 999px;
      text-decoration: none;
      white-space: nowrap;
    }}
    .nav-link-btn {{
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.8rem;
      font-weight: 500;
      padding: 6px 10px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      transition: all 0.15s;
    }}
    .nav-link-btn:hover {{
      color: #fff;
      background: var(--card-bg);
    }}

    /* Mobile Series Horizontal Selector Bar */
    .mobile-series-bar {{
      display: none;
      background: #0b0f14;
      border-bottom: 1px solid var(--border);
      padding: 8px 14px;
      overflow-x: auto;
      white-space: nowrap;
      scrollbar-width: none;
      -webkit-overflow-scrolling: touch;
      gap: 8px;
    }}
    .mobile-series-bar::-webkit-scrollbar {{
      display: none;
    }}
    .series-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 6px 14px;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      flex-shrink: 0;
      transition: all 0.15s;
    }}
    .series-chip.active {{
      background: var(--gold-dim);
      border-color: var(--gold);
      color: #fff;
    }}
    .series-chip .dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--gold);
    }}

    /* Main Responsive Layout */
    .main-layout {{
      display: flex;
      flex: 1;
      max-width: 1440px;
      margin: 0 auto;
      width: 100%;
    }}

    /* Sidebar Catalog (Desktop) */
    .catalog-sidebar {{
      width: var(--sidebar-w);
      border-right: 1px solid var(--border);
      background: #090c10;
      padding: 24px 16px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      flex-shrink: 0;
    }}
    .section-label {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-weight: 700;
      color: var(--text-muted);
      margin-bottom: 10px;
      padding-left: 8px;
    }}
    .book-list {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .book-nav-item {{
      background: transparent;
      border: 1px solid transparent;
      border-radius: 8px;
      padding: 10px 12px;
      text-align: left;
      cursor: pointer;
      color: var(--text);
      display: flex;
      flex-direction: column;
      gap: 2px;
      transition: all 0.15s;
    }}
    .book-nav-item:hover {{
      background: var(--card-bg);
      border-color: var(--border);
    }}
    .book-nav-item.active {{
      background: var(--gold-dim);
      border-color: var(--gold);
    }}
    .book-nav-series {{
      font-size: 0.7rem;
      color: var(--gold);
      font-weight: 700;
      text-transform: uppercase;
    }}
    .book-nav-title {{
      font-size: 0.92rem;
      font-weight: 600;
      color: #fff;
    }}
    .book-nav-meta {{
      font-size: 0.74rem;
      color: var(--text-muted);
      display: flex;
      gap: 8px;
    }}

    /* Content Area */
    .content-area {{
      flex: 1;
      padding: 28px 32px;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    /* Book Hero Banner */
    .book-hero {{
      background: linear-gradient(180deg, var(--card-bg) 0%, #0d121a 100%);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 22px 24px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 20px;
    }}
    .hero-meta {{
      flex: 1;
      min-width: 0;
    }}
    .hero-badge {{
      display: inline-block;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
      color: var(--gold);
      background: var(--gold-dim);
      padding: 3px 10px;
      border-radius: 999px;
      margin-bottom: 8px;
      border: 1px solid rgba(210, 153, 34, 0.25);
    }}
    .hero-title {{
      font-size: 1.65rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 6px;
      line-height: 1.25;
    }}
    .hero-subtitle {{
      font-size: 0.92rem;
      color: var(--text-muted);
      max-width: 720px;
      margin-bottom: 14px;
      line-height: 1.5;
    }}
    .hero-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 0.78rem;
      color: var(--text-muted);
      align-items: center;
    }}
    .hero-controls {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 10px;
      flex-shrink: 0;
    }}
    .source-selector {{
      display: inline-flex;
      background: #070a0e;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 3px;
    }}
    .source-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.78rem;
      cursor: pointer;
      font-weight: 600;
      min-height: 34px;
      transition: all 0.15s;
    }}
    .source-btn.active {{
      background: var(--gold);
      color: #000;
    }}

    /* View Switcher: Audio Playlist vs Reader */
    .view-tabs {{
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 6px;
    }}
    .tab-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      font-size: 0.9rem;
      font-weight: 600;
      padding: 10px 16px;
      border-radius: 8px;
      cursor: pointer;
      min-height: 44px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s;
    }}
    .tab-btn:hover {{
      color: #fff;
    }}
    .tab-btn.active {{
      color: var(--gold);
      background: var(--gold-dim);
      border-color: rgba(210, 153, 34, 0.3);
    }}

    /* Chapter Playlist */
    .playlist {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .chapter-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      cursor: pointer;
      min-height: 64px;
      transition: all 0.15s ease;
    }}
    .chapter-card:hover {{
      border-color: var(--gold);
      background: var(--card-hover);
    }}
    .chapter-card.active-track {{
      border-color: var(--gold);
      background: var(--gold-dim);
      box-shadow: 0 0 16px rgba(210, 153, 34, 0.15);
    }}
    .ch-left {{
      display: flex;
      align-items: center;
      gap: 14px;
      flex: 1;
      min-width: 0;
    }}
    .ch-num {{
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--gold);
      width: 28px;
      text-align: center;
      flex-shrink: 0;
    }}
    .ch-title {{
      font-size: 0.96rem;
      font-weight: 600;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-bottom: 2px;
    }}
    .ch-meta {{
      font-size: 0.76rem;
      color: var(--text-muted);
      display: flex;
      gap: 8px;
    }}
    .ch-right {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }}
    .pill {{
      font-size: 0.72rem;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .pill-live {{
      background: rgba(63, 185, 80, 0.15);
      color: var(--success);
      border: 1px solid rgba(63, 185, 80, 0.3);
    }}
    .pill-queue {{
      background: rgba(139, 148, 158, 0.12);
      color: var(--text-muted);
      border: 1px solid var(--border);
    }}
    .btn-play-sm {{
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: var(--gold);
      color: #000;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.15rem;
      font-weight: 800;
      cursor: pointer;
      flex-shrink: 0;
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
      transition: transform 0.15s ease, background 0.15s ease;
    }}
    .btn-play-sm:hover {{
      transform: scale(1.08);
      background: var(--gold-light);
    }}
    .btn-play-sm:disabled {{
      background: #1c222c;
      color: #485363;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }}

    /* Audio Equalizer Animation for Active Playing Track */
    .eq-bars {{
      display: inline-flex;
      align-items: flex-end;
      gap: 2px;
      height: 14px;
      margin-left: 6px;
      vertical-align: middle;
    }}
    .eq-bar {{
      width: 3px;
      background: var(--gold);
      border-radius: 1px;
      animation: eqBounce 1s ease-in-out infinite alternate;
    }}
    .eq-bar:nth-child(1) {{ height: 8px; animation-delay: 0.1s; }}
    .eq-bar:nth-child(2) {{ height: 14px; animation-delay: 0.3s; }}
    .eq-bar:nth-child(3) {{ height: 6px; animation-delay: 0.5s; }}
    @keyframes eqBounce {{
      0% {{ height: 4px; }}
      100% {{ height: 14px; }}
    }}

    /* Synchronized Reader Pane */
    .reader-pane {{
      display: none;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 36px 42px;
      max-width: 820px;
      margin: 0 auto;
      font-size: 1.1rem;
      line-height: 1.85;
      color: #d1d7e0;
      box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }}
    .reader-pane.active {{
      display: block;
    }}
    .reader-header {{
      margin-bottom: 24px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
    }}
    .reader-pane h1 {{
      font-size: 1.85rem;
      color: #fff;
      line-height: 1.3;
      margin: 28px 0 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border);
    }}
    .reader-pane h1:first-child {{
      margin-top: 0;
    }}
    .reader-pane h2 {{
      font-size: 1.5rem;
      color: #fff;
      line-height: 1.35;
      margin: 32px 0 14px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
    }}
    .reader-pane h3 {{
      font-size: 1.3rem;
      color: #fff;
      margin: 26px 0 10px;
    }}
    .reader-pane h4, .reader-pane h5 {{
      font-size: 1.12rem;
      color: var(--gold);
      margin: 20px 0 8px;
    }}
    .reader-pane p {{
      margin-bottom: 20px;
      letter-spacing: -0.003em;
    }}
    .reader-pane strong {{
      color: #fff;
      font-weight: 700;
    }}
    .reader-pane em {{
      color: #e6edf3;
      font-style: italic;
    }}
    .reader-pane blockquote {{
      border-left: 3px solid var(--gold);
      background: rgba(210, 153, 34, 0.07);
      padding: 14px 20px;
      margin: 22px 0;
      border-radius: 0 8px 8px 0;
      font-style: italic;
      color: #e6edf3;
    }}
    .reader-pane blockquote p:last-child {{
      margin-bottom: 0;
    }}
    .reader-pane ul, .reader-pane ol {{
      padding-left: 28px;
      margin: 16px 0 22px;
    }}
    .reader-pane li {{
      margin-bottom: 8px;
      padding-left: 4px;
    }}
    .reader-pane hr {{
      border: none;
      border-top: 1px solid var(--border);
      margin: 36px 0;
    }}
    .reader-pane table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      font-size: 0.95rem;
      display: block;
      overflow-x: auto;
    }}
    .reader-pane th, .reader-pane td {{
      padding: 10px 14px;
      border: 1px solid var(--border);
      text-align: left;
    }}
    .reader-pane th {{
      background: rgba(255, 255, 255, 0.05);
      color: #fff;
      font-weight: 700;
    }}
    .reader-pane code {{
      background: rgba(255, 255, 255, 0.08);
      color: var(--gold-light);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.88em;
    }}
    .reader-pane pre {{
      background: #06090e;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      margin: 20px 0;
    }}
    .reader-pane pre code {{
      background: transparent;
      padding: 0;
      color: #e6edf3;
    }}
    .reader-pane a {{
      color: var(--accent);
      text-decoration: none;
    }}
    .reader-pane a:hover {{
      text-decoration: underline;
    }}
    .reader-pane .footnote {{
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
      font-size: 0.88rem;
      color: var(--text-muted);
    }}
    .reader-pane .footnote-ref {{
      font-size: 0.78rem;
      color: var(--gold);
      vertical-align: super;
      text-decoration: none;
      padding: 0 2px;
      font-weight: 600;
    }}
    .reader-pane .footnote-backref {{
      color: var(--gold);
      text-decoration: none;
      margin-left: 4px;
    }}

    /* Synchronized Read-Along Highlighting */
    .sync-segment {{
      cursor: pointer;
      border-radius: 6px;
      padding: 6px 12px;
      margin-left: -12px;
      margin-right: -12px;
      border-left: 3px solid transparent;
      transition: background 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
      position: relative;
    }}
    .sync-segment:hover {{
      background: rgba(255, 255, 255, 0.04);
    }}
    .sync-segment.active-segment {{
      background: rgba(210, 153, 34, 0.14) !important;
      border-left: 3px solid var(--gold) !important;
      color: #fff !important;
      box-shadow: 0 0 20px rgba(210, 153, 34, 0.12);
    }}
    .reader-pane h1.sync-segment,
    .reader-pane h2.sync-segment,
    .reader-pane h3.sync-segment {{
      padding-top: 8px;
      padding-bottom: 8px;
      margin-top: 20px;
    }}
    .reader-pane li.sync-segment {{
      padding: 4px 10px;
      margin-left: -10px;
      border-radius: 4px;
      border-left: 3px solid transparent;
      transition: background 0.2s ease, border-color 0.2s ease;
    }}
    .reader-pane li.sync-segment.active-segment {{
      background: rgba(210, 153, 34, 0.14) !important;
      border-left: 3px solid var(--gold) !important;
      color: #fff !important;
    }}
    .reader-pane tr.sync-segment {{
      cursor: pointer;
      transition: background 0.2s ease, border-color 0.2s ease;
    }}
    .reader-pane tr.sync-segment:hover {{
      background: rgba(255, 255, 255, 0.05);
    }}
    .reader-pane tr.sync-segment.active-segment {{
      background: rgba(210, 153, 34, 0.18) !important;
      color: #fff !important;
    }}
    .reader-pane tr.sync-segment.active-segment td:first-child {{
      border-left: 3px solid var(--gold) !important;
    }}
    .reader-pane table.sync-segment {{
      border: 1px solid var(--border);
      border-radius: 8px;
      transition: all 0.25s ease;
    }}
    .reader-pane table.sync-segment.active-segment {{
      border: 2px solid var(--gold) !important;
      background: rgba(210, 153, 34, 0.05);
      box-shadow: 0 0 24px rgba(210, 153, 34, 0.2);
    }}
    .non-spoken,
    [data-spoken="false"] {{
      opacity: 0.85;
    }}
    .sync-indicator {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.74rem;
      font-weight: 600;
      color: var(--gold);
      background: var(--gold-dim);
      border: 1px solid rgba(210, 153, 34, 0.3);
      padding: 4px 10px;
      border-radius: 999px;
      cursor: pointer;
      user-select: none;
      transition: all 0.15s;
    }}
    .sync-indicator:hover {{
      background: rgba(210, 153, 34, 0.22);
    }}
    .sync-indicator.disabled {{
      color: var(--text-muted);
      border-color: var(--border);
      background: transparent;
    }}

    /* Marketing & Patreon Tier Blueprint */
    .patreon-blueprint {{
      background: #090e15;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 22px 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .patreon-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .patreon-title {{
      font-size: 1.05rem;
      font-weight: 700;
      color: #fff;
    }}
    .tier-cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
    }}
    .tier-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .tier-card h4 {{
      color: var(--gold);
      font-size: 0.95rem;
    }}
    .tier-card p {{
      font-size: 0.82rem;
      color: var(--text-muted);
      line-height: 1.5;
    }}
    .tier-links {{
      margin-top: auto;
      padding-top: 8px;
      font-size: 0.82rem;
    }}
    .tier-links a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}
    .tier-links a:hover {{
      text-decoration: underline;
    }}

    /* Persistent Mobile-First Bottom Player Dock */
    .player-dock {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(7, 10, 14, 0.97);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-top: 1px solid var(--border);
      padding: 10px 18px calc(10px + var(--safe-bottom));
      box-shadow: 0 -8px 30px rgba(0,0,0,0.8);
      z-index: 1000;
    }}
    .dock-inner {{
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    /* Touch-friendly Progress Track */
    .dock-progress-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.74rem;
      color: var(--text-muted);
      font-variant-numeric: tabular-nums;
    }}
    .touch-scrubber-area {{
      flex: 1;
      padding: 8px 0;
      cursor: pointer;
      display: flex;
      align-items: center;
    }}
    .bar-bg {{
      width: 100%;
      height: 6px;
      background: #1e2633;
      border-radius: 3px;
      position: relative;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      background: linear-gradient(90deg, #d29922, #f1e05a);
      border-radius: 3px;
      width: 0%;
      transition: width 0.1s linear;
    }}

    .dock-main {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
    }}
    .dock-info {{
      flex: 1;
      min-width: 0;
    }}
    .dock-title {{
      font-size: 0.94rem;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.3;
    }}
    .dock-sub {{
      font-size: 0.72rem;
      color: var(--gold);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.2;
    }}
    .dock-ctrls {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }}
    .btn-dock {{
      background: transparent;
      border: none;
      color: var(--text);
      font-size: 0.95rem;
      cursor: pointer;
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      transition: all 0.15s;
    }}
    .btn-dock:hover {{
      color: var(--gold);
      background: rgba(255,255,255,0.05);
    }}
    .btn-dock-play {{
      background: var(--gold);
      color: #000;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      font-size: 1.25rem;
      font-weight: 800;
      box-shadow: 0 2px 10px rgba(210, 153, 34, 0.4);
    }}
    .btn-dock-play:hover {{
      background: var(--gold-light);
      transform: scale(1.05);
    }}
    .dock-speed {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      font-size: 0.76rem;
      font-weight: 600;
      border-radius: 6px;
      padding: 6px 6px;
      min-height: 38px;
      cursor: pointer;
    }}

    /* Mobile Responsive Breakpoints */
    @media (max-width: 860px) {{
      .main-layout {{
        flex-direction: column;
      }}
      .catalog-sidebar {{
        display: none; /* Replaced by top mobile chip bar */
      }}
      .mobile-series-bar {{
        display: flex;
      }}
      .content-area {{
        padding: 16px;
        gap: 18px;
      }}
      .book-hero {{
        flex-direction: column;
        padding: 18px;
        gap: 16px;
      }}
      .hero-controls {{
        align-items: stretch;
        width: 100%;
      }}
      .source-selector {{
        width: 100%;
        display: flex;
      }}
      .source-btn {{
        flex: 1;
        text-align: center;
      }}
      .hero-title {{
        font-size: 1.45rem;
      }}
      .reader-pane {{
        padding: 20px 16px;
        font-size: 1.05rem;
      }}
      .nav-link-btn {{
        display: none;
      }}
      .ch-title {{
        font-size: 0.92rem;
      }}
      .dock-main {{
        gap: 10px;
      }}
      .dock-title {{
        font-size: 0.88rem;
      }}
      .dock-main {{
        gap: 12px;
      }}
      .dock-title {{
        font-size: 0.90rem;
      }}
      .btn-dock {{
        width: 44px;
        height: 44px;
        min-width: 44px;
        min-height: 44px;
        font-size: 0.92rem;
        touch-action: manipulation;
      }}
      .btn-dock-play {{
        width: 50px;
        height: 50px;
        min-width: 50px;
        min-height: 50px;
        font-size: 1.25rem;
        touch-action: manipulation;
      }}
      .dock-speed {{
        min-height: 44px;
        min-width: 46px;
        padding: 4px 6px;
        font-size: 0.82rem;
        touch-action: manipulation;
      }}
      .touch-scrubber-area {{
        padding: 12px 0;
        touch-action: none;
      }}
    }}

    @media (max-width: 520px) {{
      :root {{
        --dock-h: 128px;
      }}
      body {{
        padding-bottom: calc(var(--dock-h) + var(--safe-bottom) + 20px);
      }}
      .dock-main {{
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
      }}
      .dock-info {{
        text-align: center;
      }}
      .dock-ctrls {{
        justify-content: center;
        gap: 8px;
      }}
      .ch-title {{
        white-space: normal;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }}
      .chapter-card {{
        padding: 12px 12px;
      }}
    }}
  </style>
</head>
<body>
  <!-- Top Imprint Bar (Aligned Navigation) -->
  <nav class="navbar">
    <div style="display: flex; align-items: center; gap: 14px;">
      <a href="/site" class="brand">
        <div class="brand-mark">R</div>
        <div class="brand-text">
          <h1>Realized Press</h1>
          <p>Publishing Imprint & Audio Hub</p>
        </div>
      </a>
    </div>
    <div style="display: flex; align-items: center; gap: 6px; background: rgba(0,0,0,0.4); padding: 4px; border-radius: 8px; border: 1px solid var(--border);">
      <a href="/site" class="nav-link-btn" style="background: var(--gold-dim); color: var(--gold-light); font-weight: 600; border: 1px solid rgba(245,158,11,0.3);">Imprint Audio</a>
      <a href="/ide" class="nav-link-btn">Epistemic IDE</a>
      <a href="/read/parenthood-atlas/01-before-the-child-is-born" class="nav-link-btn">Serial Reader</a>
    </div>
    <div class="nav-actions">
      <span class="nav-badge" id="nav-badge-status">v1.0-rc1</span>
      <a href="https://linear.app/realized/team/ARC/projects/all" target="_blank" class="nav-link-btn">Linear ARC ↗</a>
    </div>
  </nav>

  <!-- Mobile Top Series Selector Chips -->
  <div class="mobile-series-bar" id="mobile-series-bar">
    <!-- Populated by JS -->
  </div>

  <div class="main-layout">
    <!-- Desktop Sidebar: Multi-Series Catalog -->
    <aside class="catalog-sidebar">
      <div>
        <div class="section-label">Select Series & Volume</div>
        <div class="book-list" id="book-nav-list">
          <!-- Populated by JS -->
        </div>
      </div>

      <div style="margin-top: auto; padding-top: 16px; border-top: 1px solid var(--border); font-size: 0.74rem; color: var(--text-muted); line-height: 1.5;">
        <p><strong style="color: var(--gold);">Epistemic Contract:</strong> OKF v0.2 atomic evidence cards, 3-lens calibration, 0% padding guarantee.</p>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="content-area">
      <!-- Book Hero Section -->
      <section class="book-hero">
        <div class="hero-meta">
          <div class="hero-badge" id="hero-badge">Series Title</div>
          <h2 class="hero-title" id="hero-title">Book Title</h2>
          <p class="hero-subtitle" id="hero-subtitle">Subtitle</p>
          <div class="hero-tags" id="hero-tags">
            <span id="hero-stat-chapters">0 chapters</span>
            <span>•</span>
            <span id="hero-stat-words">0 words</span>
            <span>•</span>
            <span id="hero-stat-audio">Audio available</span>
          </div>
        </div>
        <div class="hero-controls">
          <div class="source-selector">
            <button class="source-btn active" id="btn-src-online" onclick="setSource('online')">Cloud Stream</button>
            <button class="source-btn" id="btn-src-local" onclick="setSource('local')">Local Audio</button>
          </div>
        </div>
      </section>

      <!-- View Selector (Playlist vs Reader Mode) -->
      <div class="view-tabs">
        <button class="tab-btn active" id="tab-playlist" onclick="switchView('playlist')">
          <span>🎧</span>
          <span>Chapter Playlist</span>
        </button>
        <button class="tab-btn" id="tab-reader" onclick="switchView('reader')">
          <span>📖</span>
          <span>Synchronized Reader</span>
        </button>
      </div>

      <!-- Playlist View -->
      <section class="playlist" id="playlist-view">
        <!-- Rendered by JS -->
      </section>

      <!-- Reader View -->
      <section class="reader-pane" id="reader-view">
        <div class="reader-header" id="reader-header">
          <!-- Rendered by JS -->
        </div>
        <div id="reader-content">
          Select a chapter to read alongside the audio narration.
        </div>
      </section>

      <!-- Marketing & Serial-Membership Foundation -->
      <section class="patreon-blueprint">
        <div class="patreon-header">
          <h3 class="patreon-title">Reader Community & Serialization Blueprint</h3>
          <span style="font-size: 0.74rem; color: var(--gold); font-weight: 700; text-transform: uppercase;">Owned Marketing Site</span>
        </div>
        <div class="tier-cards">
          <div class="tier-card">
            <h4>1. Public Evidence Briefs</h4>
            <p>Freely available 2-page synthesis briefs distilled from stable OKF v0.2 cards for top-of-funnel organic search.</p>
            <div class="tier-links">
              <a href="https://github.com/{repo}/releases/download/v1.0-rc1/parenthood-atlas-evidence-briefs-compendium.pdf" target="_blank">Download Compendium PDF →</a>
            </div>
          </div>
          <div class="tier-card">
            <h4>2. Core Serial Chapters & Audio</h4>
            <p>Early access chapter preprints, audio drops (Gemini Flash TTS), and developmental fact-check dossiers.</p>
            <div class="tier-links">
              <a href="https://github.com/{repo}/releases/download/v1.0-rc1/01-before-the-child-is-born.mp3" target="_blank">Stream Ch 1 MP3 →</a>
            </div>
          </div>
          <div class="tier-card">
            <h4>3. Insider Reader Edition</h4>
            <p>Complete unpadded review editions (PDF + EPUB 3) and direct feedback loop into Amazon KDP release locks.</p>
            <div class="tier-links">
              <a href="https://github.com/{repo}/releases/download/v1.0-rc1/parenthood-atlas-reader-edition.pdf" target="_blank">Reader Edition PDF →</a>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <!-- Persistent Bottom Player Dock -->
  <footer class="player-dock">
    <div class="dock-inner">
      <!-- Touch-Friendly Full-Width Progress Scrubber -->
      <div class="dock-progress-row">
        <span id="time-cur">0:00</span>
        <div class="touch-scrubber-area" id="scrubber-area" onclick="seek(event)">
          <div class="bar-bg">
            <div class="bar-fill" id="bar-fill"></div>
          </div>
        </div>
        <span id="time-total">0:00</span>
      </div>

      <div class="dock-main">
        <div class="dock-info">
          <div class="dock-title" id="dock-title">Select a track to play</div>
          <div class="dock-sub" id="dock-sub">Gemini 2.5 Flash TTS Narration</div>
        </div>
        <div class="dock-ctrls">
          <button class="btn-dock" onclick="skip(-15)" title="Rewind 15 seconds" aria-label="Rewind 15 seconds">↺ 15s</button>
          <button class="btn-dock btn-dock-play" id="btn-dock-play" onclick="togglePlay()" aria-label="Play or pause">▶</button>
          <button class="btn-dock" onclick="skip(15)" title="Forward 15 seconds" aria-label="Forward 15 seconds">15s ↻</button>
          <select class="dock-speed" id="dock-speed" onchange="setSpeed(this.value)" aria-label="Playback speed">
            <option value="0.75">0.75x</option>
            <option value="1.0" selected>1.0x</option>
            <option value="1.25">1.25x</option>
            <option value="1.5">1.5x</option>
            <option value="1.75">1.75x</option>
            <option value="2.0">2.0x</option>
          </select>
        </div>
      </div>
    </div>
  </footer>

  <audio id="audio" preload="metadata"></audio>

  <script>
    const catalog = {catalog_json};
    let currentBookIdx = 0;
    let currentChapterIdx = 0;
    let streamMode = 'online';
    let currentView = 'playlist';

    const audio = document.getElementById('audio');
    const dockTitle = document.getElementById('dock-title');
    const dockSub = document.getElementById('dock-sub');
    const dockPlay = document.getElementById('btn-dock-play');
    const timeCur = document.getElementById('time-cur');
    const timeTotal = document.getElementById('time-total');
    const barFill = document.getElementById('bar-fill');

    function init() {{
      const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname) ||
                          window.location.hostname.startsWith('192.168.') ||
                          window.location.hostname.startsWith('10.') ||
                          window.location.protocol === 'file:';
      if (isLocalHost) {{
        streamMode = 'local';
        const btnLocal = document.getElementById('btn-src-local');
        const btnOnline = document.getElementById('btn-src-online');
        if (btnLocal && btnOnline) {{
          btnLocal.classList.add('active');
          btnOnline.classList.remove('active');
        }}
      }}

      const pIdx = catalog.findIndex(b => b.id === 'parenthood-atlas');
      if (pIdx >= 0) currentBookIdx = pIdx;

      renderBookNav();
      renderMobileChips();
      selectBook(currentBookIdx);
      setupMediaSession();
    }}

    function renderBookNav() {{
      const navList = document.getElementById('book-nav-list');
      navList.innerHTML = '';
      catalog.forEach((b, idx) => {{
        const btn = document.createElement('button');
        btn.className = 'book-nav-item' + (idx === currentBookIdx ? ' active' : '');
        btn.onclick = () => selectBook(idx);
        btn.innerHTML = `
          <span class="book-nav-series">${{b.seriesTitle}}</span>
          <span class="book-nav-title">${{b.title}}</span>
          <span class="book-nav-meta">
            <span>${{b.chapters.length}} ch</span>
            ${{b.hasAudio ? '<span>• Audio live</span>' : ''}}
          </span>
        `;
        navList.appendChild(btn);
      }});
    }}

    function renderMobileChips() {{
      const bar = document.getElementById('mobile-series-bar');
      bar.innerHTML = '';
      catalog.forEach((b, idx) => {{
        const chip = document.createElement('button');
        chip.className = 'series-chip' + (idx === currentBookIdx ? ' active' : '');
        chip.onclick = () => selectBook(idx);
        chip.innerHTML = `
          ${{b.hasAudio ? '<span class="dot"></span>' : ''}}
          <span>${{b.title}}</span>
        `;
        bar.appendChild(chip);
      }});
    }}

    function selectBook(idx) {{
      currentBookIdx = idx;
      currentChapterIdx = 0;
      renderBookNav();
      renderMobileChips();
      const book = catalog[idx];

      document.getElementById('hero-badge').innerText = book.seriesTitle;
      document.getElementById('hero-title').innerText = book.title;
      document.getElementById('hero-subtitle').innerText = book.subtitle;
      document.getElementById('hero-stat-chapters').innerText = `${{book.chapters.length}} chapters`;
      const totalWords = book.chapters.reduce((sum, c) => sum + c.words, 0);
      document.getElementById('hero-stat-words').innerText = `${{totalWords.toLocaleString()}} words`;
      document.getElementById('hero-stat-audio').innerText = book.hasAudio ? 'Audio Narration Active' : 'Narration Queued';

      renderPlaylist();
      if (book.chapters.length > 0) {{
        loadTrack(0, false);
      }}
    }}

    function renderPlaylist() {{
      const book = catalog[currentBookIdx];
      const container = document.getElementById('playlist-view');
      container.innerHTML = '';

      if (book.chapters.length === 0) {{
        container.innerHTML = `<div style="padding: 32px; text-align: center; color: var(--text-muted); background: var(--card-bg); border-radius: 8px;">Chapters currently in research & drafting phase.</div>`;
        return;
      }}

      book.chapters.forEach((ch, idx) => {{
        const isAvailable = streamMode === 'online' ? (ch.stem === '01-before-the-child-is-born' || ch.hasLocalMp3) : (ch.hasLocalMp3 || ch.hasLocalWav);
        const isPlaying = idx === currentChapterIdx && !audio.paused;
        const card = document.createElement('div');
        card.className = 'chapter-card' + (idx === currentChapterIdx ? ' active-track' : '');
        card.onclick = () => {{
          loadTrack(idx, isAvailable);
          if (currentView === 'reader') updateReader();
        }};
        card.innerHTML = `
          <div class="ch-left">
            <div class="ch-num">${{String(ch.num).padStart(2, '0')}}</div>
            <div style="min-width: 0;">
              <div class="ch-title">
                ${{ch.title}}
                ${{isPlaying ? '<span class="eq-bars"><span class="eq-bar"></span><span class="eq-bar"></span><span class="eq-bar"></span></span>' : ''}}
              </div>
              <div class="ch-meta">
                <span>${{ch.words.toLocaleString()}} words</span>
                <span>•</span>
                <span>~${{ch.minutes}} min</span>
              </div>
            </div>
          </div>
          <div class="ch-right">
            <a href="/read/${{book.id}}/${{ch.stem}}" class="nav-link-btn" style="border: 1px solid var(--border); padding: 5px 9px; border-radius: 6px; font-size: 0.72rem; text-decoration: none;" onclick="event.stopPropagation();" title="Open in 2-Pane Epistemic Reader">Reader ↗</a>
            ${{isAvailable
              ? '<span class="pill pill-live">Audio Ready</span>'
              : '<span class="pill pill-queue">Queued</span>'}}
            <button class="btn-play-sm" ${{!isAvailable ? 'disabled' : ''}}>
              ${{isPlaying ? '⏸' : '▶'}}
            </button>
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    function loadTrack(idx, autoPlay = false) {{
      currentChapterIdx = idx;
      const book = catalog[currentBookIdx];
      const ch = book.chapters[idx];
      if (!ch) return;

      dockTitle.innerText = `${{String(ch.num).padStart(2, '0')}}. ${{ch.title}}`;
      let url = streamMode === 'online' ? ch.onlineUrl : ch.localUrl;
      if (streamMode === 'local' && !url.startsWith('/') && !url.startsWith('http')) {{
        if (window.location.pathname.startsWith('/site')) {{
          url = '/site/' + url;
        }}
      }}
      audio.src = url;
      dockSub.innerText = streamMode === 'online' ? `${{book.title}} · Online Stream` : `${{book.title}} · Local Audio`;

      updateMediaSessionMetadata(ch, book);

      if (autoPlay) {{
        audio.play().catch(e => console.log('Autoplay handled:', e));
      }}
      renderPlaylist();
      updateReader();
    }}

    function togglePlay() {{
      if (!audio.src) {{
        loadTrack(0, true);
        return;
      }}
      if (audio.paused) {{
        audio.play();
      }} else {{
        audio.pause();
      }}
    }}

    function skip(sec) {{
      if (audio.duration) {{
        audio.currentTime = Math.max(0, Math.min(audio.duration, audio.currentTime + sec));
      }}
    }}

    function setSpeed(spd) {{
      audio.playbackRate = parseFloat(spd);
    }}

    function setSource(mode) {{
      streamMode = mode;
      document.getElementById('btn-src-online').classList.toggle('active', mode === 'online');
      document.getElementById('btn-src-local').classList.toggle('active', mode === 'local');
      renderPlaylist();
      if (audio.src) {{
        loadTrack(currentChapterIdx, !audio.paused);
      }}
    }}

    function switchView(view) {{
      currentView = view;
      document.getElementById('tab-playlist').classList.toggle('active', view === 'playlist');
      document.getElementById('tab-reader').classList.toggle('active', view === 'reader');
      document.getElementById('playlist-view').style.display = view === 'playlist' ? 'flex' : 'none';
      document.getElementById('reader-view').classList.toggle('active', view === 'reader');
      if (view === 'reader') updateReader();
    }}

    function updateReader() {{
      const book = catalog[currentBookIdx];
      const ch = book.chapters[currentChapterIdx];
      if (!ch) return;

      document.getElementById('reader-header').innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
          <span style="font-size: 0.76rem; color: var(--gold); text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em;">
            ${{book.title}} · Chapter ${{ch.num}} of ${{book.chapters.length}}
          </span>
          <div style="display: flex; align-items: center; gap: 8px;">
            <button id="btn-autoscroll" onclick="toggleAutoScroll()" class="sync-indicator">📜 Auto-Scroll: ON</button>
            <button onclick="switchView('playlist')" style="background: transparent; border: 1px solid var(--border); color: var(--text-muted); border-radius: 6px; padding: 4px 10px; font-size: 0.76rem; font-weight: 600; cursor: pointer;">
              ← Playlist
            </button>
          </div>
        </div>
        <div style="font-size: 0.82rem; color: var(--text-muted); display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
          <span>${{ch.words.toLocaleString()}} words</span>
          <span>•</span>
          <span>~${{ch.minutes}} min narration</span>
          ${{ch.hasLocalMp3 || ch.stem === '01-before-the-child-is-born' ? '<span>• 🎧 Narration Live (Tap any text to jump audio)</span>' : ''}}
        </div>
      `;
      const readerContent = document.getElementById('reader-content');
      readerContent.innerHTML = ch.transcriptHtml;

      if (window.renderMathInElement) {{
        renderMathInElement(readerContent, {{
          delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}},
            {{left: '\\\\(', right: '\\\\)', display: false}},
            {{left: '\\\\[', right: '\\\\]', display: true}}
          ],
          throwOnError: false
        }});
      }}
    }}

    function formatTime(s) {{
      if (isNaN(s)) return "0:00";
      const m = Math.floor(s / 60);
      const rem = Math.floor(s % 60);
      return `${{m}}:${{rem < 10 ? '0' : ''}}${{rem}}`;
    }}

    function seek(e) {{
      const rect = document.getElementById('scrubber-area').getBoundingClientRect();
      const pos = (e.clientX - rect.left) / rect.width;
      if (audio.duration) {{
        audio.currentTime = Math.max(0, Math.min(audio.duration, pos * audio.duration));
      }}
    }}

    /* MediaSession API for Native Mobile Lock Screen & Control Center */
    function setupMediaSession() {{
      if ('mediaSession' in navigator) {{
        navigator.mediaSession.setActionHandler('play', () => audio.play());
        navigator.mediaSession.setActionHandler('pause', () => audio.pause());
        navigator.mediaSession.setActionHandler('seekbackward', () => skip(-15));
        navigator.mediaSession.setActionHandler('seekforward', () => skip(15));
        navigator.mediaSession.setActionHandler('previoustrack', () => {{
          if (currentChapterIdx > 0) loadTrack(currentChapterIdx - 1, true);
        }});
        navigator.mediaSession.setActionHandler('nexttrack', () => {{
          const book = catalog[currentBookIdx];
          if (currentChapterIdx + 1 < book.chapters.length) loadTrack(currentChapterIdx + 1, true);
        }});
      }}
    }}

    function updateMediaSessionMetadata(ch, book) {{
      if ('mediaSession' in navigator) {{
        navigator.mediaSession.metadata = new MediaMetadata({{
          title: `${{String(ch.num).padStart(2, '0')}}. ${{ch.title}}`,
          artist: book.title,
          album: "Realized Press Audiobook",
          artwork: [
            {{ src: 'https://github.com/{repo}/raw/main/series/parenthood-atlas/publishing/parenthood-atlas-kdp-cover.pdf', sizes: '512x512', type: 'image/png' }}
          ]
        }});
      }}
    }}

    audio.addEventListener('play', () => {{
      dockPlay.innerText = '⏸';
      renderPlaylist();
    }});

    audio.addEventListener('pause', () => {{
      dockPlay.innerText = '▶';
      renderPlaylist();
    }});

    let autoScrollEnabled = true;
    let userScrollTimer = null;

    function toggleAutoScroll() {{
      autoScrollEnabled = !autoScrollEnabled;
      const btn = document.getElementById('btn-autoscroll');
      if (btn) {{
        btn.classList.toggle('disabled', !autoScrollEnabled);
        btn.innerText = autoScrollEnabled ? '📜 Auto-Scroll: ON' : '📜 Auto-Scroll: OFF';
      }}
    }}

    function pauseUserScroll() {{
      if (!autoScrollEnabled) return;
      clearTimeout(userScrollTimer);
      userScrollTimer = setTimeout(() => {{
        userScrollTimer = null;
      }}, 5000); // Resume auto-scrolling 5s after user stops touching/scrolling
    }}

    window.addEventListener('wheel', pauseUserScroll, {{ passive: true }});
    window.addEventListener('touchmove', pauseUserScroll, {{ passive: true }});

    function updateAudioSyncHighlight(currentTime, duration) {{
      const segments = document.querySelectorAll('.sync-segment');
      if (!segments.length) return;
      const hasTimings = segments[0].hasAttribute('data-start-time');
      const ratio = duration > 0 ? (currentTime / duration) : 0;
      let active = null;

      segments.forEach(seg => {{
        let isActive = false;
        if (hasTimings && seg.hasAttribute('data-start-time')) {{
          const start = parseFloat(seg.getAttribute('data-start-time'));
          const end = parseFloat(seg.getAttribute('data-end-time'));
          isActive = (currentTime >= start && currentTime < end);
        }} else {{
          const startRatio = parseFloat(seg.getAttribute('data-start-ratio'));
          const endRatio = parseFloat(seg.getAttribute('data-end-ratio'));
          isActive = (ratio >= startRatio && ratio < endRatio);
        }}

        if (isActive) {{
          active = seg;
          seg.classList.add('active-segment');
        }} else {{
          seg.classList.remove('active-segment');
        }}
      }});

      if (active && autoScrollEnabled && !userScrollTimer) {{
        active.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      }}
    }}

    // Bidirectional seek: Tap any text segment to jump audio to that exact moment
    document.addEventListener('click', (e) => {{
      if (e.target.closest('a') || e.target.closest('button')) return;
      const seg = e.target.closest('.sync-segment');
      if (seg && currentView === 'reader') {{
        if (seg.hasAttribute('data-start-time')) {{
          const startTime = parseFloat(seg.getAttribute('data-start-time'));
          if (!isNaN(startTime)) {{
            audio.currentTime = Math.max(0, startTime);
            if (audio.paused) {{
              audio.play().catch(err => console.log('Autoplay on tap handled:', err));
            }}
          }}
        }} else {{
          const startRatio = parseFloat(seg.getAttribute('data-start-ratio'));
          if (audio.duration && !isNaN(startRatio)) {{
            audio.currentTime = Math.max(0, Math.min(audio.duration, startRatio * audio.duration));
            if (audio.paused) {{
              audio.play().catch(err => console.log('Autoplay on tap handled:', err));
            }}
          }}
        }}
      }}
    }});

    audio.addEventListener('timeupdate', () => {{
      timeCur.innerText = formatTime(audio.currentTime);
      timeTotal.innerText = formatTime(audio.duration);
      if (audio.duration) {{
        barFill.style.width = `${{(audio.currentTime / audio.duration) * 100}}%`;
        if (currentView === 'reader') {{
          updateAudioSyncHighlight(audio.currentTime, audio.duration);
        }}
      }}
    }});

    audio.addEventListener('ended', () => {{
      const book = catalog[currentBookIdx];
      if (currentChapterIdx + 1 < book.chapters.length) {{
        loadTrack(currentChapterIdx + 1, true);
      }}
    }});

    init();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render interactive HTML5 audiobook web player & imprint portal.")
    parser.add_argument("book", nargs="?", default=None, type=Path, help="Specific book directory (optional)")
    parser.add_argument("--imprint", action="store_true", help="Generate centralized imprint-wide multi-series portal")
    parser.add_argument("--output", default="dist/site", help="Output directory for static imprint export (default: dist/site)")
    parser.add_argument("--release-tag", default="v1.0-rc1", help="GitHub Release tag for online streaming (default: v1.0-rc1)")
    parser.add_argument("--repo", default=DEFAULT_GITHUB_REPO, help="GitHub repository (owner/repo)")
    args = parser.parse_args()

    root = repo_root()

    if args.imprint or args.book is None:
        catalog = scan_all_imprint_books(root, args.repo)
        portal_html = render_portal_html(catalog, args.repo)

        out_dir = root / args.output
        out_dir.mkdir(parents=True, exist_ok=True)
        portal_file = out_dir / "index.html"
        portal_file.write_text(portal_html, encoding="utf-8")

        # Also write to docs/ for zero-config GitHub Pages
        docs_dir = root / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        docs_file = docs_dir / "index.html"
        docs_file.write_text(portal_html, encoding="utf-8")

        # Copy any generated audio files into site directory for direct local streaming
        for audio_mp3 in root.glob("series/**/audiobook/*.mp3"):
            dest = out_dir / audio_mp3.name
            if not dest.exists() or audio_mp3.stat().st_mtime > dest.stat().st_mtime:
                shutil.copy2(audio_mp3, dest)
                print(f"[imprint] Synced audio: {audio_mp3.name} -> {out_dir.name}/")

        print(f"[imprint] Rendered Mobile-First Centralized Imprint Portal across {len(catalog)} volumes:")
        for b in catalog:
            print(f"  - {b['seriesTitle']}: {b['title']} ({len(b['chapters'])} chapters)")
        print(f"Outputs written to:")
        print(f"  - {portal_file}")
        print(f"  - {docs_file}")
        return

    # Book-specific mode
    book_path = resolve_book_path(root, args.book)
    catalog = [collect_book_data(book_path, book_path.name.title(), "Field Guide & Reference", args.release_tag, args.repo)]
    book_html = render_portal_html(catalog, args.repo)

    pub_dir = book_path / "publishing"
    aud_dir = book_path / "audiobook"
    pub_dir.mkdir(parents=True, exist_ok=True)
    aud_dir.mkdir(parents=True, exist_ok=True)

    out1 = pub_dir / "audiobook-player.html"
    out2 = aud_dir / "index.html"
    out1.write_text(book_html, encoding="utf-8")
    out2.write_text(book_html, encoding="utf-8")

    print(f"[book] Wrote single-book player to:")
    print(f"  - {out1}")
    print(f"  - {out2}")


if __name__ == "__main__":
    main()
