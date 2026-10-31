# bwe/analytics.py
"""Realized Press — BWE Static & Interactive Editorial Analytics Engine (ARC-80 / P-ARC-18).

Computes search cluster distribution, Gini/HHI concentration, BM25 coverage quadrants,
commercial CPC bid velocity, and bibliographic recency metrics across imprint series,
exporting 4-panel publication-grade 300-DPI PNG and vector SVG decks.
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


def compute_series_analytics(
    series_slug: str, root: Path = REPO_ROOT, lang: Optional[str] = None
) -> dict[str, Any]:
    """Compute comprehensive quantitative analytics for a series."""
    # Ensure scripts dir is in sys.path
    import sys
    scripts_dir = root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import marketing_intelligence as mi

    base_slug = series_slug.split("/i18n/")[0]
    effective_lang = lang or mi.detect_series_language(series_slug, root)
    seed_csv = mi.resolve_seed_csv_path(series_slug, root)
    
    # Initialize DB and collect signals
    bwedb.init_db(root)
    signals, _candidates = mi.collect_signals(seed_csv, series_slug, lang=effective_lang)

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

    if is_aom:
        for s in signals:
            book_key = s.target_chapter.split("/")[0] if "/" in s.target_chapter else "book-01-vanishing-signal"
            groups.setdefault(book_key, []).append(s)
        # Sort by book order
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
        })

    gini_gkp = gini_coefficient(gkp_vols)
    gini_tot = gini_coefficient(tot_vols)
    hhi_gkp = herfindahl_index(gkp_vols)
    hhi_tot = herfindahl_index(tot_vols)

    # Bibliographic recency
    series_path = root / "series" / base_slug
    bib_years = extract_series_bib_years(series_path)
    post_2015 = sum(1 for y in bib_years if y >= 2015)
    post_2020 = sum(1 for y in bib_years if y >= 2020)

    decades_dict: dict[int, int] = {}
    for y in bib_years:
        d = (y // 10) * 10
        decades_dict[d] = decades_dict.get(d, 0) + 1

    # Book metadata for AOM
    book_meta = []
    if is_aom:
        b_dirs = sorted([d for d in series_path.iterdir() if d.is_dir() and d.name.startswith("book-")])
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

    # KDP Boxes
    title_text = "Parenthood: The Atlas" if not is_aom else "The Architectures of Memory"
    kdp_boxes, kdp_cap, kdp_tot = mi.pack_kdp_boxes(signals, title_text, lang=effective_lang)

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
        "gini_verified": round(gini_gkp, 3),
        "gini_total": round(gini_tot, 3),
        "hhi_verified": round(hhi_gkp, 0),
        "hhi_total": round(hhi_tot, 0),
        "bib_years": bib_years,
        "bib_count": len(bib_years),
        "bib_post_2015_count": post_2015,
        "bib_post_2015_pct": round(post_2015 / len(bib_years) * 100.0, 1) if bib_years else 0.0,
        "bib_post_2020_count": post_2020,
        "bib_post_2020_pct": round(post_2020 / len(bib_years) * 100.0, 1) if bib_years else 0.0,
        "decades": decades_dict,
        "book_meta": book_meta,
        "kdp_boxes": kdp_boxes,
        "kdp_captured_pct": round(kdp_cap / kdp_tot * 100.0, 1) if kdp_tot else 0.0,
        "signals": signals,
    }


def export_static_analytics_deck(
    series_slug: str, output_dir: Path, root: Path = REPO_ROOT, lang: Optional[str] = None
) -> dict[str, Path]:
    """Render and export publication-grade static 4-panel PNG (300 DPI) and SVG decks."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = compute_series_analytics(series_slug, root=root, lang=lang)
    is_aom = data["is_aom"]
    breakdown = data["breakdown"]

    fig = plt.figure(figsize=(16, 11), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.34, wspace=0.26)

    # Panel A: Demand Volume (Verified vs Seed)
    ax1 = fig.add_subplot(gs[0, 0])
    y_pos = np.arange(len(breakdown))
    labels = [b["label"] for b in breakdown]
    v_gkp = [b["verified_vol"] / 1000.0 for b in breakdown]
    v_seed = [b["seed_vol"] / 1000.0 for b in breakdown]

    ax1.barh(y_pos, v_gkp, height=0.55, label="Verified GKP Vol (k/mo)", color="#1D4ED8", edgecolor="#1E3A8A")
    ax1.barh(y_pos, v_seed, left=v_gkp, height=0.55, label="Unverified Seed Vol (k/mo)", color="#CBD5E1", edgecolor="#64748B", hatch="//")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=8.5, fontweight="bold", color="#1E293B")
    ax1.set_xlabel("Monthly Search Volume (Thousands / mo)", fontsize=9.5, fontweight="bold")
    title_a = (
        f"A. 15-Chapter Demand Reach: Verified GKP vs. Seed (Gini = {data['gini_verified']})"
        if not is_aom
        else f"A. 5-Volume Demand Reach: Verified GKP vs. Seed (Total = {data['combined_volume']/1000:.1f}k/mo)"
    )
    ax1.set_title(title_a, fontsize=11, fontweight="bold", color="#0F172A", pad=10)
    ax1.legend(loc="lower right", fontsize=8.5, frameon=True)
    ax1.grid(axis="x", linestyle="--", alpha=0.5)

    max_x = max([b["total_vol"] / 1000.0 for b in breakdown] or [10.0])
    for idx, b in enumerate(breakdown):
        tot_k = b["total_vol"] / 1000.0
        pct = b["verified_pct"]
        ax1.text(tot_k + (max_x * 0.015), idx, f"{tot_k:.1f}k ({pct:.0f}% GKP)", va="center", fontsize=7.5, fontweight="bold", color="#1E293B")
    ax1.set_xlim(0, max_x * 1.18)

    # Panel B: Editorial Opportunity Quadrant (Coverage vs Volume)
    ax2 = fig.add_subplot(gs[0, 1])
    sigs = data["signals"]
    gkp_sigs = [s for s in sigs if s.source_tier != "seed"]
    seed_sigs = [s for s in sigs if s.source_tier == "seed"]

    if gkp_sigs:
        sc1 = ax2.scatter(
            [s.coverage for s in gkp_sigs],
            [max(10, s.monthly_volume) for s in gkp_sigs],
            s=[np.clip(math.sqrt(s.opportunity_score) * 1.8, 18, 260) for s in gkp_sigs],
            c=[np.clip(s.cpc_high_usd, 0, 14) for s in gkp_sigs],
            cmap="viridis", alpha=0.78, edgecolors="#0F172A", linewidth=0.5, label="Verified GKP Cluster"
        )
        cbar = plt.colorbar(sc1, ax=ax2, pad=0.02)
        cbar.set_label("Top-of-Page CPC Bid ($ USD)", fontsize=8.5, fontweight="bold")

    if seed_sigs:
        ax2.scatter(
            [s.coverage for s in seed_sigs],
            [max(10, s.monthly_volume) for s in seed_sigs],
            s=[np.clip(math.sqrt(s.opportunity_score) * 1.5, 25, 220) for s in seed_sigs],
            color="#F59E0B", marker="D", alpha=0.85, edgecolors="#78350F", linewidth=0.8, label="Tier-3 Seed Cluster"
        )

    ax2.set_yscale("log")
    ax2.axvline(0.50, color="#DC2626", linestyle="--", linewidth=1.2, label="Coverage Gate (0.50)")
    ax2.axhline(1000, color="#64748B", linestyle=":", linewidth=1.0)
    ax2.set_xlabel("Continuous FTS5 BM25 Coverage Score (0.00 - 1.00)", fontsize=9.5, fontweight="bold")
    ax2.set_ylabel("Monthly Search Volume (Log10 Scale)", fontsize=9.5, fontweight="bold")
    ax2.set_title("B. Editorial Opportunity Quadrant (Coverage vs. Log Vol, Color = CPC)", fontsize=11, fontweight="bold", color="#0F172A", pad=10)
    ax2.legend(loc="lower left", fontsize=8, frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.set_xlim(0.20, 1.03)

    # Panel C: Commercial Intent OR Epistemic Apparatus
    ax3 = fig.add_subplot(gs[1, 0])
    if not is_aom:
        max_cpcs = [b["max_cpc"] for b in breakdown]
        mean_cpcs = [b["mean_cpc"] for b in breakdown]
        ax3.barh(y_pos + 0.18, max_cpcs, height=0.35, label="Max Top-of-Page CPC ($ USD)", color="#047857", edgecolor="#065F46")
        ax3.barh(y_pos - 0.18, mean_cpcs, height=0.35, label="Mean Top-of-Page CPC ($ USD)", color="#6EE7B7", edgecolor="#059669")
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(labels, fontsize=8.5, fontweight="bold", color="#1E293B")
        ax3.set_xlabel("Google Ads Top-of-Page Bid ($ USD)", fontsize=9.5, fontweight="bold")
        ax3.set_title("C. Commercial Intent by Chapter (CPC Bid Ceiling & Mean)", fontsize=11, fontweight="bold", color="#0F172A", pad=10)
        ax3.legend(loc="lower right", fontsize=8.5, frameon=True)
        ax3.grid(axis="x", linestyle="--", alpha=0.5)
        cpc_lim = max(max_cpcs or [5.0])
        for idx, b in enumerate(breakdown):
            if b["max_cpc"] > 0:
                ax3.text(b["max_cpc"] + 0.2, idx + 0.18, f"${b['max_cpc']:.2f}", va="center", fontsize=7.5, fontweight="bold", color="#047857")
        ax3.set_xlim(0, max(cpc_lim * 1.18, 5.0))
    else:
        bm = data["book_meta"]
        x_b = np.arange(len(bm))
        w_b = 0.20
        b_codes = [b["short"] for b in bm]
        ax3.bar(x_b - 1.5*w_b, [b["chapters"] for b in bm], width=w_b, label="Chapters", color="#1E40AF")
        ax3.bar(x_b - 0.5*w_b, [b["cards"] for b in bm], width=w_b, label="OKF v0.2 Cards", color="#059669")
        ax3.bar(x_b + 0.5*w_b, [b["bib_sources"] for b in bm], width=w_b, label="BibTeX Sources", color="#7C3AED")
        ax3.bar(x_b + 1.5*w_b, [b["fact_checks"] for b in bm], width=w_b, label="Fact-Check Dossiers", color="#DC2626")
        ax3.set_xticks(x_b)
        ax3.set_xticklabels(b_codes, fontsize=9, fontweight="bold")
        ax3.set_ylabel("Artifact Count per Volume", fontsize=9.5, fontweight="bold")
        ax3.set_title("C. Multi-Volume Apparatus Symmetry (Books 1–5)", fontsize=11, fontweight="bold", color="#0F172A", pad=10)
        ax3.legend(loc="upper right", fontsize=8, frameon=True)
        ax3.grid(axis="y", linestyle="--", alpha=0.5)

    # Panel D: Bibliographic Velocity & Recency Distribution
    ax4 = fig.add_subplot(gs[1, 1])
    dec_dict = data["decades"]
    decades = sorted(dec_dict.keys())
    dec_counts = [dec_dict[d] for d in decades]
    dec_labels = [f"{d}s" for d in decades]
    colors_dec = ["#94A3B8" if d < 2010 else ("#2563EB" if d == 2010 else "#059669") for d in decades]
    bars_d = ax4.bar(dec_labels, dec_counts, color=colors_dec, edgecolor="#1E293B", width=0.6)
    ax4.set_xlabel(f"Publication Decade (sources.bib, n = {data['bib_count']} Verified Sources)", fontsize=9.5, fontweight="bold")
    ax4.set_ylabel("Locked Primary Sources (Count)", fontsize=9.5, fontweight="bold")
    ax4.set_title(
        f"D. Bibliographic Velocity ({data['bib_post_2015_pct']}% Post-2015 | {data['bib_post_2020_pct']}% Post-2020)",
        fontsize=11, fontweight="bold", color="#0F172A", pad=10
    )
    ax4.grid(axis="y", linestyle="--", alpha=0.5)
    plt.setp(ax4.get_xticklabels(), rotation=30, ha="right", fontsize=8)
    for bar in bars_d:
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2, h + 0.5, f"{int(h)}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#1E293B")
    ax4.set_ylim(0, max(dec_counts or [10]) + 6)

    title_main = (
        f"STATIC ANALYTICS DECK — {series_slug.upper()} ({data['total_clusters']} Clusters | {data['verified_clusters_pct']}% GKP Verified)"
    )
    plt.suptitle(title_main, fontsize=13.5, fontweight="bold", color="#0F172A", y=0.97)

    png_path = output_dir / "analytics_deck.png"
    svg_path = output_dir / "analytics_deck.svg"
    plt.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)

    return {"png": png_path, "svg": svg_path}
