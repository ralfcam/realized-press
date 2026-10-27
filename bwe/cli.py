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
def intelligence(discover: str = typer.Option(None, help="Upstream topic discovery query via OpenAlex")):
    """ARC-58: Run Marketing Intelligence & Citation Telemetry synthesis."""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "marketing_intelligence.py")]
    if discover:
        cmd.extend(["--discover", discover])
    rc = subprocess.call(cmd)
    raise typer.Exit(code=rc)


if __name__ == "__main__":
    cli()
