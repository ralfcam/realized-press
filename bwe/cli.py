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
    dry_run: bool = typer.Option(False, "--dry-run", help="Do not write the seed CSV or series.yaml"),
):
    """ARC-58 / ARC-72 / ARC-73 / ARC-78: Run Marketing Intelligence, Keyword Demand Telemetry & KDP Optimizer."""
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
    if dry_run:
        cmd.append("--dry-run")
    rc = subprocess.call(cmd)
    raise typer.Exit(code=rc)


if __name__ == "__main__":
    cli()
