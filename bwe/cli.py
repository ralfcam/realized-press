# bwe/cli.py
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import typer
import uvicorn
from bwe.schema import export_json_schema, validate_series_yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

cli = typer.Typer(help="Realized Press — Book Writing Environment (BWE) CLI (ARC-56)")
REPO_ROOT = Path(__file__).resolve().parent.parent


@cli.command()
def serve(host: str = "0.0.0.0", port: int = 8080, reload: bool = True):
    """Launch the BWE Epistemic IDE & Serial Reader Portal (with LAN auto-detection)."""
    import socket

    lan_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    typer.echo("\n=======================================================")
    typer.echo("🚀 Realized Press — BWE & Serial Reader Portal")
    typer.echo(f"   • Local URL:   http://localhost:{port}/")
    typer.echo(f"   • Network URL: http://{lan_ip}:{port}/")
    typer.echo(f"   • Imprint Hub: http://{lan_ip}:{port}/site/")
    typer.echo(f"   • Epistemic IDE: http://{lan_ip}:{port}/ide")
    typer.echo(f"   • Analytics:   http://{lan_ip}:{port}/analytics")
    typer.echo("=======================================================\n")
    uvicorn.run("bwe.main:app", host=host, port=port, reload=reload)


@cli.command()
def validate_schema(series_slug: str = "parenthood-atlas"):
    """ARC-57: Validate series/<slug>/series.yaml and export JSON schema."""
    schema_out = REPO_ROOT / "series.schema.json"
    export_json_schema(schema_out)
    yaml_path = REPO_ROOT / "series" / series_slug / "series.yaml"
    manifest = validate_series_yaml(yaml_path)
    typer.echo(f"[PASS] Validated {manifest.title} ({len(manifest.books)} books) against {schema_out.name}")


@cli.command()
def audit(target: str = typer.Argument("series/parenthood-atlas", help="Target series or book directory")):
    """ARC-56: Run five_rule_check.py and audit_manuscript.py on a chapter or book."""
    for script in ["five_rule_check.py", "audit_manuscript.py"]:
        rc = subprocess.call([sys.executable, str(REPO_ROOT / "scripts" / script), target])
        if rc != 0:
            raise typer.Exit(code=rc)


@cli.command("export-site")
def export_site(output: str = "dist/site"):
    """Export standalone static offline imprint player and briefs to dist/site."""
    rc = subprocess.call([sys.executable, str(REPO_ROOT / "scripts" / "render_audiobook_player.py"), "--imprint", "--output", output])
    if rc != 0:
        raise typer.Exit(code=rc)
    typer.echo(f"[PASS] Successfully exported standalone static imprint to {output}")


@cli.command("cover-art")
def cover_art(
    series: str = typer.Option("parenthood-atlas", "--series", "-s", help="Series slug (e.g. parenthood-atlas or architectures-of-memory)"),
    book: str = typer.Option(None, "--book", "-b", help="Book slug for multi-volume series (e.g. book-01-vanishing-signal)"),
    layout_mode: str = typer.Option(None, "--layout-mode", help="Override CoverLayoutMode (vector_only, front_hero_vignette, front_full_bleed, full_wrap_canvas)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print synthesized prompt, aspect ratio, target DPI, and cache key without calling API"),
    draft: bool = typer.Option(False, "--draft", help="Use fast 1K preview tier (gemini-3.1-flash-lite-image)"),
    force: bool = typer.Option(False, "--force", help="Bypass cache and regenerate artwork via Gemini API"),
    render_all: bool = typer.Option(False, "--render-all", help="Generate cover art and compile KDP wrap cover + EPUB across all books in series"),
):
    """ARC-98 (BWE v1.1.0): Generate 300+ DPI Gemini cover artwork and optionally compile KDP covers & EPUBs."""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "generate_cover_art.py"), "--series", series]
    if book:
        cmd.extend(["--book", book])
    if layout_mode:
        cmd.extend(["--layout-mode", layout_mode])
    if dry_run:
        cmd.append("--dry-run")
    if draft:
        cmd.append("--draft")
    if force:
        cmd.append("--force")
    if render_all:
        cmd.append("--render-all")
    rc = subprocess.call(cmd)
    raise typer.Exit(code=rc)


@cli.command()
def intelligence(
    discover: str = typer.Option(None, help="Upstream topic discovery query via OpenAlex"),
    keywords: str = typer.Option(None, help="Google Keyword Planner CSV path (or 'seed' for data/gkp_*_seed.csv)"),
    series: str = typer.Option(None, help="Target series slug (e.g. parenthood-atlas)"),
    fetch_live: bool = typer.Option(False, "--fetch-live", help="Stage 1 autocomplete discovery -> Stage 2 Google Ads empirical enrichment"),
    expand_ideas: bool = typer.Option(False, "--expand-ideas", help="Run Google Ads GenerateKeywordIdeas on chapter topic clusters"),
    import_gkp_export: str = typer.Option(None, "--import-gkp-export", help="Path to Google Ads UI CSV export (UTF-16LE / UTF-8)"),
    optimize_kdp_boxes: bool = typer.Option(False, "--optimize-kdp-boxes", help="Pack covered demand into 7 KDP backend keyword boxes (<= 49 UTF-8 bytes)"),
    write_series_yaml: bool = typer.Option(False, "--write-series-yaml", help="Write proposed KDP 7 boxes directly into series.yaml in-place (ARC-78)"),
    lang: str = typer.Option(None, "--lang", help="Explicit language override ('en', 'es', 'fr') (ARC-78)"),
    export_amazon_ads: str = typer.Option(None, "--export-amazon-ads", help="Path to export Amazon Advertising (Sponsored Products) bulk upload CSV"),
    export_charts: str = typer.Option(None, "--export-charts", help="Export static 4-panel PNG and SVG analytics decks to output directory (ARC-80)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Do not write the seed CSV or series.yaml"),
):
    """ARC-58 / ARC-72 / ARC-73 / ARC-78 / ARC-80: Run Marketing Intelligence, Keyword Demand Telemetry, Analytics Deck & KDP Optimizer."""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "marketing_intelligence.py")]
    if discover:
        cmd.extend(["--discover", discover])
    if keywords:
        cmd.extend(["--keywords", keywords])
    if series:
        cmd.extend(["--series", series])
    if fetch_live:
        cmd.append("--fetch-live")
    if expand_ideas:
        cmd.append("--expand-ideas")
    if import_gkp_export:
        cmd.extend(["--import-gkp-export", import_gkp_export])
    if optimize_kdp_boxes:
        cmd.append("--optimize-kdp-boxes")
    if write_series_yaml:
        cmd.append("--write-series-yaml")
    if lang:
        cmd.extend(["--lang", lang])
    if export_amazon_ads:
        cmd.extend(["--export-amazon-ads", export_amazon_ads])
    if export_charts:
        cmd.extend(["--export-charts", export_charts])
    if dry_run:
        cmd.append("--dry-run")
    rc = subprocess.call(cmd)
    raise typer.Exit(code=rc)


@cli.command()
def context(
    series: str = typer.Option(..., "--series", "-s", help="Series slug (e.g. parenthood-atlas or architectures-of-memory)"),
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter slug (e.g. 05-becoming-a-mind)"),
    book: str = typer.Option(None, "--book", "-b", help="Book slug for multi-volume series (e.g. book-02-forget-gate)"),
    format: str = typer.Option("md", "--format", "-f", help="Output format: 'md' (Markdown) or 'json'"),
):
    """ARC-84: Generate token-budgeted Chapter Context Pack (CCP) from OKF v0.3 Graph RAG."""
    import json
    from bwe.graph_rag import compile_chapter_context_pack

    pack = compile_chapter_context_pack(series_slug=series, chapter_slug=chapter, book_slug=book)
    if format.lower() == "json":
        typer.echo(json.dumps(pack.to_dict(), indent=2, ensure_ascii=False))
    else:
        typer.echo(pack.to_markdown())


@cli.command()
def sculpt(
    series: str = typer.Option("parenthood-atlas", "--series", "-s", help="Series slug (e.g. parenthood-atlas or architectures-of-memory)"),
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter slug (e.g. 04-regulatory-relationship)"),
    book: str = typer.Option(None, "--book", "-b", help="Book slug for multi-volume series (e.g. book-01-vanishing-signal)"),
    lang: str = typer.Option("en", "--lang", help="Edition language ('en', 'es', 'fr')"),
    top_k: int = typer.Option(5, "--top-k", help="Number of priority paragraphs to include in sculpt pack"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print telemetry and frozen-skeleton sculpt prompts without modifying files"),
    format: str = typer.Option("md", "--format", "-f", help="Output format: 'md' or 'json'"),
):
    """ARC-104 (BWE v1.3.1): Generate Frozen-Skeleton Phrasal-Sculpting Pack & Poetics Telemetry for a chapter."""
    import json
    from bwe.style_sculptor import generate_chapter_sculpt_pack

    pack = generate_chapter_sculpt_pack(
        series_slug=series,
        chapter_slug=chapter,
        book_slug=book,
        lang=lang,
        top_k=top_k,
    )
    if format.lower() == "json":
        typer.echo(json.dumps(pack, indent=2, ensure_ascii=False))
        return

    typer.echo(f"# Frozen-Skeleton Phrasal-Sculpting Pack — `{pack['chapter_slug']}` ({pack['series_slug']})")
    typer.echo(
        f"- **Phrasal Poetics Score:** `{pack['chapter_poetics_score']}/100` | "
        f"**Copula Ratio:** `{pack['copula_ratio']:.1%}` | "
        f"**Nominalization Clusters:** `{pack['nominalization_clusters']}` | "
        f"**Tail Drags:** `{pack['participial_tail_drags']}` | "
        f"**Avg Cadence σ:** `{pack['avg_cadence_sigma']}w`"
    )
    if pack["canonical_metaphors"]:
        typer.echo(f"- **OKF v0.3 Canonical Metaphors:** {', '.join(f'`{m}`' for m in pack['canonical_metaphors'])}")
    typer.echo(f"- **Priority Paragraphs Queued:** `{pack['target_count']}`\n")
    for idx, t in enumerate(pack["targets"], 1):
        typer.echo(f"---\n### Target {idx}: Paragraph `[p.{t['paragraph_index']}]` ({t['words']}w, {t['sentences']}s, Score `{t['poetics_score']}`)")
        typer.echo(t["sculpt_prompt"])


@cli.command()
def graph(
    series: str = typer.Option("architectures-of-memory", "--series", "-s", help="Series slug"),
    book: str = typer.Option(None, "--book", "-b", help="Book slug filter (e.g. book-01-vanishing-signal)"),
    stats: bool = typer.Option(False, "--stats", help="Display graph topology and node/edge statistics"),
    gaps: bool = typer.Option(False, "--gaps", help="List high-volume demand clusters (monthly_volume >= 1000) with lowest graph coverage weight"),
    lineage: list[str] = typer.Option(None, "--lineage", "-l", help="Two card slugs to trace shortest epistemic lineage: --lineage <src> <dst>"),
    subgraph: str = typer.Option(None, "--subgraph", help="Seed card or chapter slug to extract k-hop ego subgraph"),
    hops: int = typer.Option(2, "--hops", help="Max hops for subgraph or lineage (default: 2 for subgraph, 8 for lineage)"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: 'table' or 'json'"),
):
    """ARC-90 / ARC-91: Graph RAG Introspection — topology stats, shortest-path lineage, k-hop subgraphs, and demand gaps."""
    import json
    from bwe.db import get_db, ensure_series_graph
    from bwe.graph_rag import find_epistemic_lineage, query_k_hop_subgraph

    conn = get_db()
    ensure_series_graph(conn, REPO_ROOT, series)

    if gaps:
        where_kw = "WHERE series_slug = ? AND monthly_volume >= 1000"
        gap_rows = conn.execute(
            f"""SELECT query, monthly_volume, cpc_high_usd, bm25_coverage_score, bm25_chapter_score, bm25_card_score, matched_card, matched_chapter
               FROM keyword_signals {where_kw}
               ORDER BY bm25_coverage_score ASC, monthly_volume DESC LIMIT 15""",
            (series,),
        ).fetchall()

        low_coverage = [
            r for r in gap_rows
            if (r["bm25_coverage_score"] or 0.0) < 0.45 or (r["bm25_card_score"] or 0.0) < 0.45
        ]
        target_display = low_coverage if low_coverage else gap_rows[:10]

        if format.lower() == "json":
            typer.echo(json.dumps([dict(r) for r in target_display], indent=2, ensure_ascii=False))
        else:
            typer.echo(f"\n[GRAPH DEMAND GAPS] Series: '{series}' (monthly_volume >= 1,000, ranked by coverage weight)\n" + "=" * 80)
            if not target_display:
                typer.echo("  No high-volume demand clusters found.")
            else:
                for idx, r in enumerate(target_display, 1):
                    cov = r["bm25_coverage_score"] or 0.0
                    card_cov = r["bm25_card_score"] or 0.0
                    if cov < 0.45:
                        flag = " [CRITICAL GAP < 0.45]"
                    elif card_cov < 0.45:
                        flag = " [Chapter-Covered / Card-Thin]"
                    else:
                        flag = " [Covered]"
                    typer.echo(
                        f"  {idx:>2}. '{r['query']}' | Vol: {r['monthly_volume']:,}/mo | "
                        f"CPC: ${r['cpc_high_usd'] or 0.0:.2f} | Coverage Weight: {cov:.4f} (card: {card_cov:.4f}){flag} | "
                        f"Card: {r['matched_card'] or 'None'}"
                    )
            typer.echo("")
        return

    if lineage and len(lineage) >= 2:
        src, dst = lineage[0], lineage[1]
        max_h = 8 if hops == 2 else hops
        steps = find_epistemic_lineage(conn, series, src, dst, max_hops=max_h)
        if format.lower() == "json":
            typer.echo(json.dumps(steps, indent=2, ensure_ascii=False))
        else:
            typer.echo(f"\n[EPISTEMIC LINEAGE] '{src}' -> '{dst}' ({len(steps)} hops)\n" + "=" * 70)
            if not steps:
                typer.echo("  No connecting epistemic path found within hop limit.")
            for s in steps:
                dir_marker = "->" if s.get("direction") == "forward" else "<-"
                typer.echo(
                    f"  Hop {s['hop']}: {s['source_slug']} [{s['source_grade']} | {s['source_tier']}] "
                    f"--[{s['relationship']} {dir_marker}]--> {s['target_slug']} [{s['target_grade']} | {s['target_tier']}]"
                )
            typer.echo("")
        return

    if subgraph:
        res = query_k_hop_subgraph(conn, series, subgraph, max_hops=hops)
        if format.lower() == "json":
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            typer.echo(f"\n[K-HOP SUBGRAPH] Seed: '{res['seed_node_id']}' (max_hops={hops})\n" + "=" * 70)
            typer.echo(f"  Discovered: {res['node_count']} nodes, {res['edge_count']} internal edges\n")
            typer.echo("  Nodes:")
            for n in res["nodes"][:15]:
                typer.echo(f"    - [{n['node_type']}] depth {n['depth']}: {n['node_id']} ({n['label']})")
            if len(res["nodes"]) > 15:
                typer.echo(f"    ... and {len(res['nodes']) - 15} more nodes.")
            typer.echo("")
        return

    # Default to --stats
    if stats or (not lineage and not subgraph):
        where_series = "WHERE series_slug = ?"
        params: tuple = (series,)
        if book:
            where_book = "WHERE series_slug = ? AND book_slug = ?"
            params_book = (series, book)
        else:
            where_book = where_series
            params_book = params

        total_nodes = conn.execute(f"SELECT COUNT(*) FROM okf_nodes {where_book}", params_book).fetchone()[0]
        total_edges = conn.execute(f"SELECT COUNT(*) FROM okf_edges {where_series}", params).fetchone()[0]

        card_count = conn.execute(
            f"SELECT COUNT(*) FROM okf_nodes {where_book} AND node_type = 'card'",
            params_book,
        ).fetchone()[0]
        ch_count = conn.execute(
            f"SELECT COUNT(*) FROM okf_nodes {where_book} AND node_type = 'chapter'",
            params_book,
        ).fetchone()[0]
        mv_count = conn.execute(
            f"SELECT COUNT(*) FROM okf_nodes {where_book} AND node_type = 'movement'",
            params_book,
        ).fetchone()[0]
        char_count = conn.execute(
            f"SELECT COUNT(*) FROM okf_nodes {where_series} AND node_type = 'character'",
            params,
        ).fetchone()[0]
        demand_count = conn.execute(
            f"SELECT COUNT(*) FROM okf_nodes {where_series} AND node_type = 'demand'",
            params,
        ).fetchone()[0]

        # Orphaned cards count (cards with 0 incoming CITES_CARD edges)
        card_nodes = conn.execute(
            f"SELECT node_id FROM okf_nodes {where_book} AND node_type = 'card'",
            params_book,
        ).fetchall()
        orphaned_count = sum(
            1 for c in card_nodes
            if conn.execute(
                "SELECT COUNT(*) FROM okf_edges WHERE series_slug = ? AND target_id = ? AND edge_type = 'CITES_CARD'",
                (series, c["node_id"]),
            ).fetchone()[0] == 0
        )

        edge_types = conn.execute(
            f"SELECT edge_type, COUNT(*) FROM okf_edges {where_series} GROUP BY edge_type ORDER BY COUNT(*) DESC",
            params,
        ).fetchall()

        if format.lower() == "json":
            typer.echo(json.dumps({
                "series_slug": series,
                "book_slug": book or "all",
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "cards": card_count,
                "orphaned_cards": orphaned_count,
                "chapters": ch_count,
                "movements": mv_count,
                "characters": char_count,
                "demand_nodes": demand_count,
                "edge_distribution": dict(edge_types),
            }, indent=2))
        else:
            typer.echo(f"\n[OKF v0.3 KNOWLEDGE GRAPH TOPOLOGY] Series: '{series}'" + (f" | Book: '{book}'" if book else ""))
            typer.echo("=" * 70)
            typer.echo(f"  Total Nodes:    {total_nodes:,}")
            typer.echo(f"    - Evidence Cards:     {card_count} (orphaned_cards: {orphaned_count})")
            typer.echo(f"    - Chapters:           {ch_count}")
            typer.echo(f"    - Movements:          {mv_count}")
            typer.echo(f"    - Characters:         {char_count}")
            typer.echo(f"    - Demand Clusters:    {demand_count}")
            typer.echo(f"  Total Edges:    {total_edges:,}")
            typer.echo("  Edge Distribution:")
            for etype, cnt in edge_types:
                typer.echo(f"    - {etype:<25} {cnt:>5}")
            typer.echo("")


if __name__ == "__main__":
    cli()
