# bwe/analytics.py
"""Realized Press — BWE Data Analytics & Visual Telemetry Studio (ARC-80 / P-ARC-18).

Provides:
- Statistical aggregation across search clusters, BM25 coverage, opportunity scores, and CPC bids.
- Server-side SVG chart generators (Demand Quadrant Scatter, Chapter Volume & CPC Bars, 12-Month Sparklines, Decade Recency).
- Static 300-DPI publication-grade PNG and SVG exporters (individual charts + 4-panel master deck).
- Closed-loop integration with reader feedback and citation telemetry.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np

# Use non-interactive backend for headless CLI / server rendering
import matplotlib
matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

from bwe import db as bwedb

REPO_ROOT = Path(__file__).resolve().parent.parent


def gini_coefficient(array: list[float] | np.ndarray) -> float:
    """Calculate the Gini coefficient of a numpy array or list."""
    arr = np.sort(np.asarray(array, dtype=float))
    if arr.size == 0 or arr.sum() == 0:
        return 0.0
    n = len(arr)
    index = np.arange(1, n + 1)
    return float((np.sum((2 * index - n - 1) * arr)) / (n * np.sum(arr)))


def herfindahl_index(array: list[float] | np.ndarray) -> float:
    """Calculate the Herfindahl-Hirschman Index (HHI, 0 to 10,000) of search volume distribution."""
    arr = np.asarray(array, dtype=float)
    tot = arr.sum()
    if tot == 0:
        return 0.0
    shares = (arr / tot) * 100.0
    return float(np.sum(shares ** 2))


def extract_series_bib_years(series_path: Path) -> list[int]:
    """Extract publication years from all sources.bib files in a series directory."""
    years: list[int] = []
    for bib in series_path.glob("**/sources.bib"):
        if not bib.is_file():
            continue
        text = bib.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"year\s*=\s*[\"{]?(\d{4})[\"}]?", text, re.IGNORECASE):
            try:
                y = int(match.group(1))
                if 1800 <= y <= 2030:
                    years.append(y)
            except ValueError:
                pass
    return sorted(years)


def _stats_summary(values: list[float]) -> dict[str, float]:
    """Return count, sum, mean, median, min, max, std for a numeric distribution."""
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return {
            "count": 0, "sum": 0.0, "mean": 0.0, "median": 0.0,
            "min": 0.0, "max": 0.0, "std": 0.0,
        }
    return {
        "count": int(arr.size),
        "sum": float(np.sum(arr)),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "std": float(np.std(arr)) if arr.size > 1 else 0.0,
    }


def is_quick_finder_mapped(query: str, corpus: str) -> bool:
    """Check if query core tokens are covered in front-matter 2:00 AM Quick-Finder text."""
    if not corpus:
        return False
    tokens = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) >= 3]
    if not tokens:
        return False
    hits = sum(1 for t in tokens if t in corpus)
    return (hits / len(tokens)) >= 0.5


def render_sparkline_svg(
    hist_or_trend: Any,
    yoy: float = 0.0,
    vol: int = 1000,
    width: int = 90,
    height: int = 24,
    query: str = "",
) -> str:
    """Render a responsive 12-point dark-mode SVG mini sparkline."""
    points: list[float] = []
    if isinstance(hist_or_trend, str) and hist_or_trend.strip() and hist_or_trend != "[]":
        try:
            parsed = json.loads(hist_or_trend)
            if isinstance(parsed, list) and parsed:
                if isinstance(parsed[0], dict) and "monthly_searches" in parsed[0]:
                    points = [float(p.get("monthly_searches", 0)) for p in parsed]
                elif isinstance(parsed[0], (int, float)):
                    points = [float(p) for p in parsed]
        except Exception:
            pass

    if not points or len(points) < 2:
        v_end = float(vol)
        v_start = v_end / max(0.1, 1.0 + (yoy / 100.0))
        h = sum(ord(c) for c in (query or "rp")) % 17
        points = []
        for i in range(12):
            t = i / 11.0
            base = v_start + (v_end - v_start) * t
            wobble = math.sin((i + h) * 0.8) * 0.05 * v_end
            points.append(max(0.0, base + wobble))

    min_val, max_val = min(points), max(points)
    val_range = max_val - min_val if max_val > min_val else 1.0
    pad_y = 3.0
    eff_h = height - 2 * pad_y
    n = len(points)
    step_x = (width - 6.0) / (n - 1)

    coords = []
    for i, p in enumerate(points):
        x = 3.0 + i * step_x
        y = height - pad_y - ((p - min_val) / val_range) * eff_h
        coords.append((x, y))

    stroke_color = "#10B981" if yoy >= 0 else "#F43F5E"
    poly_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    last_x, last_y = coords[-1]
    area_points = f"M {coords[0][0]:.1f},{height} " + " ".join(f"L {x:.1f},{y:.1f}" for x, y in coords) + f" L {last_x:.1f},{height} Z"
    fill_color = "rgba(16, 185, 129, 0.15)" if yoy >= 0 else "rgba(244, 63, 94, 0.15)"

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" class="inline-block overflow-visible" aria-hidden="true">'
        f'<path d="{area_points}" fill="{fill_color}" />'
        f'<polyline points="{poly_points}" fill="none" stroke="{stroke_color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />'
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="2.2" fill="{stroke_color}" />'
        f'</svg>'
    )


def render_quadrant_svg(signals: list[Any], width: int = 760, height: int = 420) -> str:
    """Render dark-mode SVG Demand vs. BM25 Coverage Quadrant Scatter Plot."""
    margin_l, margin_r, margin_t, margin_b = 65, 30, 40, 50
    inner_w = width - margin_l - margin_r
    inner_h = height - margin_t - margin_b

    vols = [s.monthly_volume for s in signals if s.monthly_volume > 0]
    max_v = max(vols) if vols else 100000
    min_v = 10.0
    log_min = math.log10(min_v)
    log_max = math.log10(max(max_v, 10000))

    def map_x(cov: float) -> float:
        clamped = max(0.0, min(1.0, cov))
        return margin_l + clamped * inner_w

    def map_y(vol: int) -> float:
        v = max(min_v, float(vol))
        log_v = math.log10(v)
        norm = (log_v - log_min) / (log_max - log_min)
        return margin_t + (1.0 - norm) * inner_h

    split_x = map_x(0.50)
    split_y = map_y(5000)

    lines = [
        f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto select-none" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="#0c0a09" rx="12" stroke="#292524" stroke-width="1"/>',
        f'<rect x="{margin_l}" y="{margin_t}" width="{split_x - margin_l}" height="{split_y - margin_t}" fill="#f43f5e" fill-opacity="0.04" />',
        f'<rect x="{split_x}" y="{margin_t}" width="{margin_l + inner_w - split_x}" height="{split_y - margin_t}" fill="#10b981" fill-opacity="0.04" />',
        f'<rect x="{margin_l}" y="{split_y}" width="{split_x - margin_l}" height="{margin_t + inner_h - split_y}" fill="#64748b" fill-opacity="0.03" />',
        f'<rect x="{split_x}" y="{split_y}" width="{margin_l + inner_w - split_x}" height="{margin_t + inner_h - split_y}" fill="#38bdf8" fill-opacity="0.03" />',
        f'<line x1="{split_x}" y1="{margin_t}" x2="{split_x}" y2="{margin_t + inner_h}" stroke="#44403c" stroke-width="1.5" stroke-dasharray="4 4"/>',
        f'<line x1="{margin_l}" y1="{split_y}" x2="{margin_l + inner_w}" y2="{split_y}" stroke="#44403c" stroke-width="1.5" stroke-dasharray="4 4"/>',
        f'<text x="{margin_l + 12}" y="{margin_t + 22}" fill="#fda4af" font-size="10.5" font-family="monospace" font-weight="bold" letter-spacing="1">Q1: CONTENT GAPS (HIGH DEMAND / UNCOVERED)</text>',
        f'<text x="{margin_l + inner_w - 12}" y="{margin_t + 22}" text-anchor="end" fill="#6ee7b7" font-size="10.5" font-family="monospace" font-weight="bold" letter-spacing="1">Q2: CORE ANCHORS (HIGH DEMAND / COVERED)</text>',
        f'<text x="{margin_l + 12}" y="{margin_t + inner_h - 14}" fill="#94a3b8" font-size="10.5" font-family="monospace" font-weight="bold" letter-spacing="1">Q4: LONG TAIL (LOW DEMAND / UNCOVERED)</text>',
        f'<text x="{margin_l + inner_w - 12}" y="{margin_t + inner_h - 14}" text-anchor="end" fill="#7dd3fc" font-size="10.5" font-family="monospace" font-weight="bold" letter-spacing="1">Q3: NICHE STRENGTHS (LOW DEMAND / COVERED)</text>',
    ]

    for tick_x in [0.0, 0.25, 0.50, 0.75, 1.0]:
        px = map_x(tick_x)
        lines.append(f'<line x1="{px}" y1="{margin_t}" x2="{px}" y2="{margin_t + inner_h}" stroke="#1c1917" stroke-width="1"/>')
        lines.append(f'<text x="{px}" y="{margin_t + inner_h + 18}" text-anchor="middle" fill="#78716c" font-size="10" font-family="monospace">{tick_x:.2f}</text>')

    for tick_y in [10, 100, 1000, 10000, 100000]:
        if tick_y <= max_v * 1.5:
            py = map_y(tick_y)
            lbl = f"{tick_y:,}" if tick_y < 1000 else f"{tick_y//1000}k"
            lines.append(f'<line x1="{margin_l}" y1="{py}" x2="{margin_l + inner_w}" y2="{py}" stroke="#1c1917" stroke-width="1"/>')
            lines.append(f'<text x="{margin_l - 10}" y="{py + 3}" text-anchor="end" fill="#78716c" font-size="10" font-family="monospace">{lbl}</text>')

    lines.append(f'<text x="{margin_l + inner_w/2}" y="{height - 12}" text-anchor="middle" fill="#a8a29e" font-size="11" font-family="monospace" font-weight="bold">BM25 Chapter Coverage Score (0.00 → 1.00)</text>')
    lines.append(f'<text transform="rotate(-90) translate({-(margin_t + inner_h/2)}, 18)" text-anchor="middle" fill="#a8a29e" font-size="11" font-family="monospace" font-weight="bold">Monthly Searches (Log Scale)</text>')

    sorted_sigs = sorted(signals, key=lambda s: -s.monthly_volume)
    for s in sorted_sigs:
        cx = map_x(s.chapter_score)
        cy = map_y(s.monthly_volume)
        r = min(12.0, max(3.5, 3.0 + math.sqrt(max(0.0, s.cpc_high_usd)) * 1.6))
        
        if s.chapter_score < 0.50 and s.monthly_volume >= 5000:
            fill = "#f43f5e"
        elif s.chapter_score >= 0.50 and s.monthly_volume >= 5000:
            fill = "#10b981"
        elif s.chapter_score >= 0.50 and s.monthly_volume < 5000:
            fill = "#38bdf8"
        else:
            fill = "#94a3b8"

        cpc_str = f"${s.cpc_high_usd:.2f}" if s.cpc_high_usd > 0 else "$0.00"
        ch_str = s.target_chapter or "?"
        esc_q = s.query.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        tooltip = f"{esc_q}&#10;Volume: {s.monthly_volume:,}/mo&#10;Coverage: {s.chapter_score:.2f}&#10;Target: Ch {ch_str}&#10;Max CPC: {cpc_str}&#10;Tier: {s.source_tier}"
        
        lines.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" fill-opacity="0.8" stroke="#ffffff" stroke-width="0.75" stroke-opacity="0.4">'
            f'<title>{tooltip}</title>'
            f'</circle>'
        )

    lines.append('</svg>')
    return "".join(lines)


def render_chapter_bars_svg(breakdown: list[dict], width: int = 760, height: int = 380) -> str:
    """Render dark-mode SVG Chapter Demand Breakdown and Max CPC Bar Chart."""
    margin_l, margin_r, margin_t, margin_b = 60, 50, 45, 65
    inner_w = width - margin_l - margin_r
    inner_h = height - margin_t - margin_b

    n_bars = len(breakdown)
    if n_bars == 0:
        return f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto"><rect width="{width}" height="{height}" fill="#0c0a09" rx="12"/></svg>'

    max_vol = max((b["total_vol"] for b in breakdown), default=1000)
    max_cpc = max((b["max_cpc"] for b in breakdown), default=5.0)
    max_vol_axis = max(max_vol * 1.15, 1000.0)
    max_cpc_axis = max(max_cpc * 1.25, 2.0)

    bar_slot = inner_w / n_bars
    bar_w = min(36.0, bar_slot * 0.72)

    lines = [
        f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto select-none" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="#0c0a09" rx="12" stroke="#292524" stroke-width="1"/>',
        f'<g transform="translate({margin_l}, 24)">',
        f'<rect x="0" y="-8" width="12" height="12" rx="2" fill="#3b82f6"/>',
        f'<text x="18" y="2" fill="#cbd5e1" font-size="10" font-family="monospace">Verified GKP Vol</text>',
        f'<rect x="130" y="-8" width="12" height="12" rx="2" fill="#475569" stroke="#94a3b8" stroke-dasharray="2 2"/>',
        f'<text x="148" y="2" fill="#94a3b8" font-size="10" font-family="monospace">Curated Seed Vol</text>',
        f'<circle cx="280" cy="-2" r="4" fill="#f59e0b"/>',
        f'<line x1="270" y1="-2" x2="290" y2="-2" stroke="#f59e0b" stroke-width="2"/>',
        f'<text x="298" y="2" fill="#fcd34d" font-size="10" font-family="monospace">Max CPC Ceiling ($)</text>',
        f'</g>',
    ]

    for tick_ratio in [0.25, 0.50, 0.75, 1.0]:
        v_tick = max_vol_axis * tick_ratio
        py = margin_t + (1.0 - tick_ratio) * inner_h
        lbl = f"{int(v_tick/1000)}k" if v_tick >= 1000 else f"{int(v_tick)}"
        lines.append(f'<line x1="{margin_l}" y1="{py}" x2="{margin_l + inner_w}" y2="{py}" stroke="#1c1917" stroke-width="1"/>')
        lines.append(f'<text x="{margin_l - 8}" y="{py + 3}" text-anchor="end" fill="#78716c" font-size="9.5" font-family="monospace">{lbl}</text>')

    for tick_ratio in [0.50, 1.0]:
        cpc_tick = max_cpc_axis * tick_ratio
        py = margin_t + (1.0 - tick_ratio) * inner_h
        lines.append(f'<text x="{margin_l + inner_w + 8}" y="{py + 3}" text-anchor="start" fill="#f59e0b" font-size="9.5" font-family="monospace">${cpc_tick:.1f}</text>')

    cpc_coords = []
    for i, b in enumerate(breakdown):
        cx = margin_l + (i + 0.5) * bar_slot
        bx = cx - bar_w / 2.0
        
        gkp_h = (b["verified_vol"] / max_vol_axis) * inner_h
        seed_h = (b["seed_vol"] / max_vol_axis) * inner_h
        
        y_gkp = margin_t + inner_h - gkp_h
        y_seed = y_gkp - seed_h

        if seed_h > 0.5:
            lines.append(f'<rect x="{bx:.1f}" y="{y_seed:.1f}" width="{bar_w:.1f}" height="{seed_h:.1f}" rx="2" fill="#475569" stroke="#64748b" stroke-width="0.5" stroke-dasharray="2 2">'
                         f'<title>{b["label"]}: {b["seed_vol"]:,} Seed Volume</title></rect>')
        if gkp_h > 0.5:
            lines.append(f'<rect x="{bx:.1f}" y="{y_gkp:.1f}" width="{bar_w:.1f}" height="{gkp_h:.1f}" rx="2" fill="#3b82f6" fill-opacity="0.9">'
                         f'<title>{b["label"]}: {b["verified_vol"]:,} Verified Volume</title></rect>')

        lbl = b["key"] if str(b["key"]).startswith("B") else f"Ch {b['key']}"
        lines.append(f'<text x="{cx:.1f}" y="{margin_t + inner_h + 16}" text-anchor="middle" fill="#cbd5e1" font-size="9.5" font-family="monospace" font-weight="bold">{lbl}</text>')
        lines.append(f'<text x="{cx:.1f}" y="{margin_t + inner_h + 28}" text-anchor="middle" fill="#64748b" font-size="8.5" font-family="monospace">{b["clusters"]} cl</text>')

        cpc_norm = (b["max_cpc"] / max_cpc_axis) if max_cpc_axis > 0 else 0.0
        cpc_y = margin_t + (1.0 - cpc_norm) * inner_h
        cpc_coords.append((cx, cpc_y, b["max_cpc"]))

    if len(cpc_coords) > 1:
        line_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in cpc_coords)
        lines.append(f'<polyline points="{line_pts}" fill="none" stroke="#f59e0b" stroke-width="2.2" stroke-linejoin="round"/>')
    for cx, cy, cpc_val in cpc_coords:
        if cpc_val > 0:
            lines.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="#f59e0b" stroke="#0c0a09" stroke-width="1.5"><title>Max CPC: ${cpc_val:.2f}</title></circle>')

    lines.append('</svg>')
    return "".join(lines)


def render_bib_decade_svg(
    decades: dict[int, int],
    post_2015_pct: float = 0.0,
    post_2020_pct: float = 0.0,
    width: int = 520,
    height: int = 240,
) -> str:
    """Render dark-mode SVG Bibliographic Decade Recency Bar Chart."""
    margin_l, margin_r, margin_t, margin_b = 40, 20, 35, 45
    inner_w = width - margin_l - margin_r
    inner_h = height - margin_t - margin_b

    sorted_decades = sorted(decades.keys())
    if not sorted_decades:
        return f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto"><rect width="{width}" height="{height}" fill="#0c0a09" rx="12"/></svg>'

    max_c = max(decades.values(), default=10)
    max_c_axis = max(max_c * 1.2, 5)

    bar_slot = inner_w / len(sorted_decades)
    bar_w = min(32.0, bar_slot * 0.72)

    lines = [
        f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto select-none" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="#0c0a09" rx="12" stroke="#292524" stroke-width="1"/>',
        f'<text x="{margin_l}" y="22" fill="#f8fafc" font-size="11" font-family="monospace" font-weight="bold">Bibliographic Recency ({post_2015_pct:.1f}% ≥ 2015 | {post_2020_pct:.1f}% ≥ 2020)</text>',
    ]

    for i, dec in enumerate(sorted_decades):
        cnt = decades[dec]
        cx = margin_l + (i + 0.5) * bar_slot
        bx = cx - bar_w / 2.0
        bh = (cnt / max_c_axis) * inner_h
        by = margin_t + inner_h - bh

        if dec >= 2020:
            fill = "#6366f1"
        elif dec >= 2010:
            fill = "#0ea5e9"
        else:
            fill = "#475569"

        lines.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="2" fill="{fill}">'
                     f'<title>{dec}s: {cnt} locked sources</title></rect>')
        lines.append(f'<text x="{cx:.1f}" y="{by - 4:.1f}" text-anchor="middle" fill="#e2e8f0" font-size="9" font-family="monospace" font-weight="bold">{cnt}</text>')
        dec_lbl = f"'{str(dec)[2:]}s"
        lines.append(f'<text x="{cx:.1f}" y="{margin_t + inner_h + 16}" text-anchor="middle" fill="#94a3b8" font-size="9" font-family="monospace">{dec_lbl}</text>')

    lines.append('</svg>')
    return "".join(lines)


def build_series_analytics_payload(
    series_slug: str, root: Path = REPO_ROOT, lang: Optional[str] = None
) -> dict[str, Any]:
    """Aggregate all keyword signals, SQLite telemetry, and render SVGs into a comprehensive analytics payload."""
    import sys
    scripts_dir = root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import marketing_intelligence as mi

    base_slug = series_slug.split("/i18n/")[0]
    effective_lang = lang or mi.detect_series_language(series_slug, root)
    seed_csv = mi.resolve_seed_csv_path(series_slug, root)

    bwedb.init_db(root)
    signals, _candidates = mi.collect_signals(seed_csv, series_slug, lang=effective_lang)

    # Load front-matter text for quick-finder sync check
    series_path = root / "series" / (series_slug if (root / "series" / series_slug).is_dir() else base_slug)
    fm_path = series_path / "front-matter.md"
    fm_corpus = fm_path.read_text(encoding="utf-8", errors="replace").lower() if fm_path.is_file() else ""

    total_clusters = len(signals)
    combined_volume = sum(s.monthly_volume for s in signals)
    verified_clusters = sum(1 for s in signals if s.source_tier != mi.TIER_SEED)
    verified_volume = sum(s.monthly_volume for s in signals if s.source_tier != mi.TIER_SEED)
    seed_clusters = total_clusters - verified_clusters
    seed_volume = combined_volume - verified_volume

    covered_signals = [s for s in signals if s.covered]
    covered_clusters = len(covered_signals)
    covered_volume = sum(s.monthly_volume for s in covered_signals)

    is_aom = base_slug == "architectures-of-memory"
    groups: dict[str, list[mi.KeywordSignal]] = {}

    # Read reader feedback & citation events from SQLite
    feedback_by_ch: dict[str, int] = {}
    citations_by_ch: dict[str, int] = {}
    tot_feedback = 0
    tot_citations = 0

    with bwedb.get_db() as conn:
        for r in conn.execute(
            "SELECT chapter_slug, count(*) as cnt FROM reader_feedback WHERE series_slug = ? GROUP BY chapter_slug;",
            (series_slug,),
        ).fetchall():
            ch_k = mi.chapter_label(r["chapter_slug"])
            feedback_by_ch[ch_k] = r["cnt"]
            tot_feedback += r["cnt"]

        for r in conn.execute(
            "SELECT chapter_slug, count(*) as cnt FROM citation_telemetry WHERE series_slug = ? GROUP BY chapter_slug;",
            (series_slug,),
        ).fetchall():
            ch_k = mi.chapter_label(r["chapter_slug"])
            citations_by_ch[ch_k] = r["cnt"]
            tot_citations += r["cnt"]

    # Enrich each signal with Quick-Finder sync and sparkline SVG
    for s in signals:
        setattr(s, "quick_finder_mapped", is_quick_finder_mapped(s.query, fm_corpus))
        setattr(s, "sparkline_svg", render_sparkline_svg([], yoy=s.yoy_trend_pct, vol=s.monthly_volume, query=s.query))

    if is_aom:
        for s in signals:
            book_key = s.target_chapter.split("/")[0] if "/" in s.target_chapter else "book-01-vanishing-signal"
            groups.setdefault(book_key, []).append(s)
        sorted_keys = sorted(groups.keys())
    else:
        for s in signals:
            ch_num = mi.chapter_label(s.target_chapter)
            groups.setdefault(ch_num, []).append(s)
        sorted_keys = [f"{i:02d}" for i in range(1, 16) if f"{i:02d}" in groups]

    breakdown = []
    gkp_vols = []
    tot_vols = []

    for k in sorted_keys:
        sigs = groups[k]
        tot_v = sum(s.monthly_volume for s in sigs)
        gkp_v = sum(s.monthly_volume for s in sigs if s.source_tier != mi.TIER_SEED)
        sd_v = tot_v - gkp_v
        vols = [s.monthly_volume for s in sigs]
        cpc_highs = [s.cpc_high_usd for s in sigs if s.cpc_high_usd > 0]
        
        gkp_vols.append(gkp_v)
        tot_vols.append(tot_v)

        breakdown.append({
            "key": k,
            "label": k if is_aom else f"Ch {k}",
            "clusters": len(sigs),
            "verified_clusters": sum(1 for s in sigs if s.source_tier != mi.TIER_SEED),
            "seed_clusters": sum(1 for s in sigs if s.source_tier == mi.TIER_SEED),
            "total_vol": tot_v,
            "verified_vol": gkp_v,
            "seed_vol": sd_v,
            "mean_vol": float(np.mean(vols)) if vols else 0.0,
            "median_vol": float(np.median(vols)) if vols else 0.0,
            "max_vol": max(vols) if vols else 0,
            "std_vol": float(np.std(vols)) if len(vols) > 1 else 0.0,
            "mean_cpc": float(np.mean(cpc_highs)) if cpc_highs else 0.0,
            "max_cpc": max(cpc_highs) if cpc_highs else 0.0,
            "verified_pct": round(gkp_v / tot_v * 100.0, 1) if tot_v > 0 else 0.0,
            "opportunity_sum": sum(s.opportunity_score for s in sigs),
            "feedback_count": feedback_by_ch.get(k, 0),
            "citation_count": citations_by_ch.get(k, 0),
        })

    gini_gkp = gini_coefficient(gkp_vols)
    gini_tot = gini_coefficient(tot_vols)
    hhi_gkp = herfindahl_index(gkp_vols)
    hhi_tot = herfindahl_index(tot_vols)

    all_vols = [float(s.monthly_volume) for s in signals]
    all_covs = [float(s.chapter_score) for s in signals]
    all_opps = [float(s.opportunity_score) for s in signals]
    all_cpcs = [float(s.cpc_high_usd) for s in signals if s.cpc_high_usd > 0]

    series_stats = {
        "volume": _stats_summary(all_vols),
        "coverage": _stats_summary(all_covs),
        "opportunity": _stats_summary(all_opps),
        "cpc": _stats_summary(all_cpcs),
    }

    bib_years = extract_series_bib_years(root / "series" / base_slug)
    post_2015 = sum(1 for y in bib_years if y >= 2015)
    post_2020 = sum(1 for y in bib_years if y >= 2020)
    post_2015_pct = round(post_2015 / len(bib_years) * 100.0, 1) if bib_years else 0.0
    post_2020_pct = round(post_2020 / len(bib_years) * 100.0, 1) if bib_years else 0.0

    decades_dict: dict[int, int] = {}
    for y in bib_years:
        d = (y // 10) * 10
        decades_dict[d] = decades_dict.get(d, 0) + 1

    book_meta = []
    if is_aom:
        b_dirs = sorted([d for d in (root / "series" / base_slug).iterdir() if d.is_dir() and d.name.startswith("book-")])
        for bd in b_dirs:
            ch_count = len([f for f in (bd / "chapters").glob("*.md") if not f.name.startswith("_")])
            card_count = len([f for f in (bd / "evidence-cards").glob("*.md") if not f.name.startswith("_") and f.name.lower() not in {"index.md", "readme.md"}])
            fc_count = len([f for f in (bd / "research" / "fact-checks").glob("*.md") if not f.name.startswith(".")])
            bib_f = bd / "research" / "sources.bib"
            bib_cnt = len(re.findall(r"^@[a-zA-Z]+\{", bib_f.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)) if bib_f.exists() else 0
            book_meta.append({
                "book": bd.name,
                "short": bd.name.replace("book-0", "B0").split("-")[0],
                "chapters": ch_count,
                "cards": card_count,
                "bib_sources": bib_cnt,
                "fact_checks": fc_count,
            })

    title_text = "Parenthood: The Atlas" if not is_aom else "The Architectures of Memory"
    kdp_boxes, kdp_cap, kdp_tot = mi.pack_kdp_boxes(signals, title_text, lang=effective_lang)

    kdp_boxes_meta = []
    for idx, box in enumerate(kdp_boxes, start=1):
        byte_len = len(box.encode("utf-8"))
        kdp_boxes_meta.append({
            "box_index": idx,
            "text": box,
            "bytes": byte_len,
            "utilization_pct": round(byte_len / 50.0 * 100.0, 1),
            "is_valid": byte_len <= 49,
        })

    valid_boxes_count = sum(1 for b in kdp_boxes_meta if b["is_valid"])
    market_readiness = f"{valid_boxes_count}/7"

    quadrant_svg = render_quadrant_svg(signals)
    chapter_bars_svg = render_chapter_bars_svg(breakdown)
    bib_decade_svg = render_bib_decade_svg(decades_dict, post_2015_pct, post_2020_pct)

    return {
        "series_slug": series_slug,
        "base_slug": base_slug,
        "language": effective_lang,
        "is_aom": is_aom,
        "total_clusters": total_clusters,
        "combined_volume": combined_volume,
        "verified_clusters": verified_clusters,
        "verified_volume": verified_volume,
        "verified_volume_pct": round(verified_volume / combined_volume * 100.0, 1) if combined_volume else 0.0,
        "verified_clusters_pct": round(verified_clusters / total_clusters * 100.0, 1) if total_clusters else 0.0,
        "seed_clusters": seed_clusters,
        "seed_volume": seed_volume,
        "covered_clusters": covered_clusters,
        "covered_volume": covered_volume,
        "coverage_rate_pct": round(covered_clusters / total_clusters * 100.0, 1) if total_clusters else 0.0,
        "breakdown": breakdown,
        "series_stats": series_stats,
        "gini_verified": round(gini_gkp, 3),
        "gini_total": round(gini_tot, 3),
        "hhi_verified": round(hhi_gkp, 0),
        "hhi_total": round(hhi_tot, 0),
        "bib_years": bib_years,
        "bib_count": len(bib_years),
        "bib_post_2015_count": post_2015,
        "bib_post_2015_pct": post_2015_pct,
        "bib_post_2020_count": post_2020,
        "bib_post_2020_pct": post_2020_pct,
        "decades": decades_dict,
        "book_meta": book_meta,
        "kdp_boxes": kdp_boxes,
        "kdp_boxes_meta": kdp_boxes_meta,
        "kdp_captured_pct": round(kdp_cap / kdp_tot * 100.0, 1) if kdp_tot else 0.0,
        "market_readiness": market_readiness,
        "signals": signals,
        "quadrant_svg": quadrant_svg,
        "chapter_bars_svg": chapter_bars_svg,
        "bib_decade_svg": bib_decade_svg,
        "total_reader_feedback": tot_feedback,
        "total_citation_events": tot_citations,
    }


def compute_series_analytics(
    series_slug: str, root: Path = REPO_ROOT, lang: Optional[str] = None
) -> dict[str, Any]:
    """Alias for backwards compatibility with earlier BWE callers."""
    return build_series_analytics_payload(series_slug, root=root, lang=lang)


def export_static_charts(
    series_slug: str, output_dir: Path, root: Path = REPO_ROOT, lang: Optional[str] = None
) -> dict[str, Path]:
    """Render publication-grade 300-DPI PNGs and SVGs for all individual charts and master deck."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = build_series_analytics_payload(series_slug, root=root, lang=lang)
    breakdown = data["breakdown"]
    is_aom = data["is_aom"]
    signals = data["signals"]

    out_paths: dict[str, Path] = {}

    # 1. Demand Quadrant Scatter (PNG + SVG)
    fig1, ax = plt.subplots(figsize=(9, 6), dpi=300)
    fig1.patch.set_facecolor("#FFFFFF")
    vols = [s.monthly_volume for s in signals]
    covs = [s.chapter_score for s in signals]
    cpcs = [s.cpc_high_usd for s in signals]
    scatter_colors = ["#10B981" if c >= 0.5 and v >= 5000 else "#F43F5E" if c < 0.5 and v >= 5000 else "#38BDF8" if c >= 0.5 else "#94A3B8" for c, v in zip(covs, vols)]
    sizes = [max(18, min(160, 20 + math.sqrt(max(0, cpc)) * 18)) for cpc in cpcs]
    ax.scatter(covs, vols, c=scatter_colors, s=sizes, alpha=0.7, edgecolors="#1E293B", linewidths=0.5)
    ax.set_yscale("log")
    ax.axvline(0.5, color="#DC2626", linestyle="--", alpha=0.7, label="Coverage Threshold (0.50)")
    ax.axhline(5000, color="#64748B", linestyle=":", alpha=0.7, label="High-Demand Threshold (5k/mo)")
    ax.set_xlabel("BM25 Chapter Coverage Score (0.00 → 1.00)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Monthly Searches (Log Scale)", fontsize=10, fontweight="bold")
    ax.set_title(f"Demand vs. BM25 Coverage Quadrant — {series_slug.upper()}", fontsize=11, fontweight="bold", pad=10)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8.5)
    p_quad_png = output_dir / "demand_quadrant.png"
    p_quad_svg = output_dir / "demand_quadrant.svg"
    plt.savefig(p_quad_png, bbox_inches="tight", dpi=300)
    plt.savefig(p_quad_svg, bbox_inches="tight")
    plt.close(fig1)
    out_paths["demand_quadrant_png"] = p_quad_png
    out_paths["demand_quadrant_svg"] = p_quad_svg

    # 2. Chapter Volume & CPC Ceiling (PNG + SVG)
    fig2, ax1 = plt.subplots(figsize=(10, 5), dpi=300)
    fig2.patch.set_facecolor("#FFFFFF")
    x_pos = np.arange(len(breakdown))
    labels = [b["label"] for b in breakdown]
    v_gkp = [b["verified_vol"] / 1000.0 for b in breakdown]
    v_seed = [b["seed_vol"] / 1000.0 for b in breakdown]
    cpcs = [b["max_cpc"] for b in breakdown]

    ax1.bar(x_pos, v_gkp, width=0.55, label="Verified GKP (k/mo)", color="#1D4ED8", edgecolor="#1E3A8A")
    ax1.bar(x_pos, v_seed, bottom=v_gkp, width=0.55, label="Curated Seed (k/mo)", color="#CBD5E1", edgecolor="#64748B", hatch="//")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(labels, rotation=35, ha="right", fontsize=8.5, fontweight="bold")
    ax1.set_ylabel("Monthly Volume (Thousands / mo)", fontsize=10, fontweight="bold", color="#1E3A8A")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    ax2 = ax1.twinx()
    ax2.plot(x_pos, cpcs, color="#D97706", marker="o", linewidth=2.0, label="Max CPC ($)")
    ax2.set_ylabel("Max CPC Intent ($ USD)", fontsize=10, fontweight="bold", color="#D97706")
    ax2.set_ylim(0, max(cpcs or [5]) * 1.3)
    ax1.set_title(f"Chapter Demand Volume & CPC Ceiling — {series_slug.upper()}", fontsize=11, fontweight="bold", pad=10)
    p_ch_png = output_dir / "chapter_volume_cpc.png"
    p_ch_svg = output_dir / "chapter_volume_cpc.svg"
    plt.savefig(p_ch_png, bbox_inches="tight", dpi=300)
    plt.savefig(p_ch_svg, bbox_inches="tight")
    plt.close(fig2)
    out_paths["chapter_volume_cpc_png"] = p_ch_png
    out_paths["chapter_volume_cpc_svg"] = p_ch_svg

    # 3. KDP 7-Box Byte Utilization (PNG + SVG)
    fig3, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    fig3.patch.set_facecolor("#FFFFFF")
    boxes = data["kdp_boxes_meta"]
    b_indices = [f"Box {b['box_index']}" for b in boxes]
    b_bytes = [b["bytes"] for b in boxes]
    y_pos = np.arange(len(boxes))
    ax.barh(y_pos, b_bytes, height=0.55, color="#7C3AED", edgecolor="#5B21B6")
    ax.axvline(50, color="#DC2626", linestyle="--", linewidth=1.5, label="KDP 50-Byte Ceiling")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(b_indices, fontsize=9, fontweight="bold")
    ax.set_xlabel("UTF-8 Byte Count (≤ 49 B)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 55)
    for i, b_len in enumerate(b_bytes):
        ax.text(b_len + 0.8, i, f"{b_len} B", va="center", fontsize=8.5, fontweight="bold", color="#1E293B")
    ax.set_title(f"Amazon KDP 7-Box Utilization ({data['kdp_captured_pct']}% Covered Demand Captured)", fontsize=11, fontweight="bold", pad=10)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right", fontsize=8.5)
    p_kdp_png = output_dir / "kdp_7box_bytes.png"
    p_kdp_svg = output_dir / "kdp_7box_bytes.svg"
    plt.savefig(p_kdp_png, bbox_inches="tight", dpi=300)
    plt.savefig(p_kdp_svg, bbox_inches="tight")
    plt.close(fig3)
    out_paths["kdp_7box_bytes_png"] = p_kdp_png
    out_paths["kdp_7box_bytes_svg"] = p_kdp_svg

    # 4. Bibliographic Recency (PNG + SVG)
    fig4, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    fig4.patch.set_facecolor("#FFFFFF")
    dec_keys = sorted(data["decades"].keys())
    dec_counts = [data["decades"][k] for k in dec_keys]
    dec_labels = [f"{k}s" for k in dec_keys]
    x_dec = np.arange(len(dec_keys))
    colors = ["#4338CA" if k >= 2020 else "#0284C7" if k >= 2010 else "#64748B" for k in dec_keys]
    bars = ax.bar(x_dec, dec_counts, width=0.55, color=colors, edgecolor="#0F172A")
    ax.set_xticks(x_dec)
    ax.set_xticklabels(dec_labels, rotation=30, ha="right", fontsize=9, fontweight="bold")
    ax.set_ylabel("Locked Primary Sources (Count)", fontsize=10, fontweight="bold")
    ax.set_title(f"Bibliographic Recency ({data['bib_post_2015_pct']}% ≥ 2015 | {data['bib_post_2020_pct']}% ≥ 2020)", fontsize=11, fontweight="bold", pad=10)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + 0.4, f"{int(h)}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    p_bib_png = output_dir / "bib_recency.png"
    p_bib_svg = output_dir / "bib_recency.svg"
    plt.savefig(p_bib_png, bbox_inches="tight", dpi=300)
    plt.savefig(p_bib_svg, bbox_inches="tight")
    plt.close(fig4)
    out_paths["bib_recency_png"] = p_bib_png
    out_paths["bib_recency_svg"] = p_bib_svg

    # 5. Master 4-Panel Deck (PNG + SVG)
    fig5 = plt.figure(figsize=(16, 11), dpi=300)
    fig5.patch.set_facecolor("#FFFFFF")
    gs = gridspec.GridSpec(2, 2, figure=fig5, hspace=0.34, wspace=0.26)

    # Panel A: Demand
    ax1 = fig5.add_subplot(gs[0, 0])
    y_pos = np.arange(len(breakdown))
    ax1.barh(y_pos, v_gkp, height=0.55, label="Verified GKP Vol (k/mo)", color="#1D4ED8", edgecolor="#1E3A8A")
    ax1.barh(y_pos, v_seed, left=v_gkp, height=0.55, label="Curated Seed Vol (k/mo)", color="#CBD5E1", edgecolor="#64748B", hatch="//")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=8.5, fontweight="bold", color="#1E293B")
    ax1.set_xlabel("Monthly Search Volume (Thousands / mo)", fontsize=9.5, fontweight="bold")
    ax1.set_title(f"A. Demand Reach (Verified vs. Seed | Gini = {data['gini_verified']})", fontsize=11, fontweight="bold", pad=10)
    ax1.grid(axis="x", linestyle="--", alpha=0.5)
    ax1.legend(loc="lower right", fontsize=8)

    # Panel B: Gini Concentration
    ax2 = fig5.add_subplot(gs[0, 1])
    sorted_vols = np.sort(np.asarray([b["verified_vol"] for b in breakdown], dtype=float))
    cum_vols = np.cumsum(sorted_vols)
    if cum_vols[-1] > 0:
        cum_vols_norm = np.insert(cum_vols / cum_vols[-1], 0, 0.0)
    else:
        cum_vols_norm = np.linspace(0, 1, len(sorted_vols) + 1)
    pop_norm = np.linspace(0, 1, len(cum_vols_norm))
    ax2.plot(pop_norm, cum_vols_norm, color="#1D4ED8", linewidth=2.5, label=f"Verified GKP Lorenz (Gini = {data['gini_verified']})")
    ax2.plot([0, 1], [0, 1], color="#DC2626", linestyle="--", linewidth=1.5, label="Perfect Demand Parity (Gini = 0.0)")
    ax2.fill_between(pop_norm, pop_norm, cum_vols_norm, color="#1D4ED8", alpha=0.15)
    ax2.set_xlabel("Cumulative Share of Chapters / Volumes", fontsize=9.5, fontweight="bold")
    ax2.set_ylabel("Cumulative Share of Verified Volume", fontsize=9.5, fontweight="bold")
    ax2.set_title(f"B. Demand Inequality (HHI = {data['hhi_verified']:.0f})", fontsize=11, fontweight="bold", pad=10)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left", fontsize=8)

    # Panel C: Quadrant Scatter
    ax3 = fig5.add_subplot(gs[1, 0])
    ax3.scatter(covs, vols, c=scatter_colors, s=sizes, alpha=0.7, edgecolors="#1E293B", linewidths=0.5)
    ax3.set_yscale("log")
    ax3.axvline(0.5, color="#DC2626", linestyle="--", alpha=0.7)
    ax3.axhline(5000, color="#64748B", linestyle=":", alpha=0.7)
    ax3.set_xlabel("BM25 Chapter Coverage Score (0.00 → 1.00)", fontsize=9.5, fontweight="bold")
    ax3.set_ylabel("Monthly Searches (Log Scale)", fontsize=9.5, fontweight="bold")
    ax3.set_title(f"C. Demand vs. BM25 Coverage Quadrant", fontsize=11, fontweight="bold", pad=10)
    ax3.grid(True, linestyle="--", alpha=0.5)

    # Panel D: Bibliographic Velocity
    ax4 = fig5.add_subplot(gs[1, 1])
    bars_d = ax4.bar(x_dec, dec_counts, width=0.55, color=colors, edgecolor="#0F172A")
    ax4.set_xticks(x_dec)
    ax4.set_xticklabels(dec_labels, rotation=30, ha="right", fontsize=8.5, fontweight="bold")
    ax4.set_ylabel("Locked Primary Sources (Count)", fontsize=9.5, fontweight="bold")
    ax4.set_title(f"D. Bibliographic Velocity ({data['bib_post_2015_pct']}% ≥ 2015 | {data['bib_post_2020_pct']}% ≥ 2020)", fontsize=11, fontweight="bold", pad=10)
    for b in bars_d:
        h = b.get_height()
        ax4.text(b.get_x() + b.get_width()/2, h + 0.4, f"{int(h)}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    ax4.grid(axis="y", linestyle="--", alpha=0.5)

    title_main = f"STATIC ANALYTICS DECK — {series_slug.upper()} ({data['total_clusters']} Clusters | {data['verified_clusters_pct']}% GKP Verified)"
    plt.suptitle(title_main, fontsize=13.5, fontweight="bold", color="#0F172A", y=0.97)

    p_deck_png = output_dir / "analytics_deck.png"
    p_deck_svg = output_dir / "analytics_deck.svg"
    plt.savefig(p_deck_png, bbox_inches="tight", dpi=300)
    plt.savefig(p_deck_svg, bbox_inches="tight")
    plt.close(fig5)
    out_paths["analytics_deck_png"] = p_deck_png
    out_paths["analytics_deck_svg"] = p_deck_svg
    out_paths["png"] = p_deck_png
    out_paths["svg"] = p_deck_svg

    return out_paths


def export_static_analytics_deck(
    series_slug: str, output_dir: Path, root: Path = REPO_ROOT, lang: Optional[str] = None
) -> dict[str, Path]:
    """Alias delegating to export_static_charts."""
    return export_static_charts(series_slug, output_dir, root=root, lang=lang)
