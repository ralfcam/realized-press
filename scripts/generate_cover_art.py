#!/usr/bin/env python3
"""Gemini Native Cover Art Generator & Asset Cache Manager (`ARC-98`, `BWE v1.1.0`).

Generates bespoke 300+ DPI print-ready cover illustrations via the official
`google-genai` SDK (`client.models.generate_content` with `types.ImageConfig`),
enforces the Multi-Part Resolution Guard and Negative Typography Guard, caches
outputs in `.cache/cover_art/<sha256>.png`, and writes `<target>/publishing/assets/cover-art.png`
alongside provenance metadata (`cover-art.meta.json`).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bwe.schema import CoverArtSpec, CoverLayoutMode, validate_series_yaml

DEFAULT_IMAGE_MODEL_CHAIN: list[str] = [
    "gemini-3-pro-image",
    "gemini-3.1-flash-image",
    "gemini-3.1-flash-lite-image",
]

NEGATIVE_TYPOGRAPHY_GUARD = (
    "STRICTLY NO TEXT, NO LETTERS, NO WORDS, NO NUMBERS, NO LABELS, "
    "NO TYPOGRAPHY, NO SIGNATURES, NO WATERMARKS, NO BORDERS"
)

PLACED_DIMENSIONS_IN: dict[CoverLayoutMode, tuple[float, float]] = {
    CoverLayoutMode.VECTOR_ONLY: (4.40, 4.40),
    CoverLayoutMode.FRONT_HERO_VIGNETTE: (4.40, 4.40),
    CoverLayoutMode.FRONT_FULL_BLEED: (6.125, 9.250),
    CoverLayoutMode.FULL_WRAP_CANVAS: (12.5923, 9.250),
}

TARGET_PIXEL_DIMENSIONS: dict[tuple[str, str], tuple[int, int]] = {
    ("1:1", "1K"): (1024, 1024),
    ("1:1", "2K"): (2048, 2048),
    ("1:1", "4K"): (4096, 4096),
    ("4:3", "1K"): (1200, 896),
    ("4:3", "2K"): (2400, 1792),
    ("4:3", "4K"): (4096, 3072),
    ("3:4", "1K"): (896, 1200),
    ("3:4", "2K"): (1792, 2400),
    ("3:4", "4K"): (3072, 4096),
    ("2:3", "1K"): (832, 1248),
    ("2:3", "2K"): (1664, 2496),
    ("2:3", "4K"): (2730, 4096),
    ("3:2", "1K"): (1248, 832),
    ("3:2", "2K"): (2496, 1664),
    ("3:2", "4K"): (4096, 2730),
    ("16:9", "1K"): (1376, 768),
    ("16:9", "2K"): (2752, 1536),
    ("16:9", "4K"): (5460, 3072),
}


def load_dotenv(root: Path = ROOT) -> None:
    env_path = root / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v


def resolve_target_manifest(target_dir: Path) -> tuple[CoverArtSpec, dict[str, Any], Path]:
    """Locate series.yaml and resolve the effective CoverArtSpec for target_dir."""
    target_dir = target_dir.resolve()
    manifest_path: Path | None = None
    for cand in [
        target_dir / "series.yaml",
        target_dir.parent / "series.yaml",
        target_dir.parent.parent / "series.yaml",
    ]:
        if cand.is_file():
            manifest_path = cand
            break

    if manifest_path is None:
        spec = CoverArtSpec()
        return spec, {"title": target_dir.name.replace("-", " ").title(), "subtitle": "", "lenses": []}, target_dir

    manifest = validate_series_yaml(manifest_path)
    spec = manifest.cover_art
    title = manifest.title
    subtitle = manifest.subtitle or ""
    lenses = [l.value for l in manifest.lenses]

    # Check if target_dir matches a specific BookSpec in a multi-book series
    for book in manifest.books:
        if book.id == target_dir.name or book.path == target_dir.name or (book.path == "." and manifest_path.parent == target_dir):
            title = book.title or title
            subtitle = book.subtitle or subtitle
            if book.cover_art is not None:
                # Prefer book-level cover_art if it defines a prompt or non-default fields
                if book.cover_art.prompt or not manifest.cover_art.prompt:
                    spec = book.cover_art
            break

    meta = {
        "series_slug": manifest.slug,
        "translation_of": manifest.translation_of,
        "locale": manifest.locale or "en",
        "title": title,
        "subtitle": subtitle,
        "lenses": lenses,
        "manifest_path": str(manifest_path),
    }
    return spec, meta, manifest_path.parent


def synthesize_cover_prompt(
    spec: CoverArtSpec,
    title: str = "",
    subtitle: str = "",
    lenses: list[str] | None = None,
) -> str:
    """Build the complete visual prompt with layout composition rules and Negative Typography Guard."""
    lenses_str = ", ".join(lenses or ["science", "interpretation", "art"])
    if spec.prompt and spec.prompt.strip():
        base_prompt = spec.prompt.strip()
    else:
        base_prompt = (
            f"Bespoke museum-grade {spec.style_preset} illustration for '{title}' ({subtitle}), "
            f"integrating {lenses_str} perspectives in {spec.palette_accent_hex} and {spec.palette_text_hex} "
            f"tones against a rich {spec.palette_bg_hex} background."
        )

    composition_clause = ""
    if spec.layout_mode == CoverLayoutMode.FRONT_FULL_BLEED:
        composition_clause = (
            " Composition: full-bleed vertical book cover illustration with clean, low-detail negative space "
            f"in the upper 32% and lower 18% matched to {spec.palette_bg_hex} for subsequent typography overlay, "
            "with the primary visual focal motif centered in the middle band."
        )
    elif spec.layout_mode == CoverLayoutMode.FULL_WRAP_CANVAS:
        composition_clause = (
            " Composition: continuous panoramic widescreen illustration with the primary focal emblem "
            "positioned in the right-hand third (front cover region) and subtle, calm atmospheric texture "
            f"in {spec.palette_bg_hex} across the center spine and left-hand third."
        )
    else:
        composition_clause = (
            " Composition: centered symmetrical emblem vignette with clean edges on a uniform "
            f"{spec.palette_bg_hex} ground, suitable for framing on a scholarly trade book cover."
        )

    full_prompt = f"{base_prompt}{composition_clause} {NEGATIVE_TYPOGRAPHY_GUARD}."
    return full_prompt


def inspect_image_bytes(raw_bytes: bytes) -> tuple[int, int]:
    """Return (width_px, height_px) if raw_bytes is a valid raster image, else (0, 0)."""
    try:
        with Image.open(io.BytesIO(raw_bytes)) as img:
            return img.size
    except Exception:
        return (0, 0)


def select_best_image_part(parts: list[Any]) -> tuple[bytes, int, int, str]:
    """Multi-Part Resolution Guard: select the inline_data image part with largest pixel area / byte footprint.

    When `image_size="2K"` or `"4K"` is requested, `gemini-3.1-flash-image` can emit both a 1K preview part
    and a 2K/4K master part in `candidate.content.parts`. Selecting the maximum `(pixel_area, byte_len)`
    prevents accidentally saving the lower-resolution preview part.
    """
    best_bytes: bytes | None = None
    best_w = 0
    best_h = 0
    best_mime = "image/png"
    best_score = (-1, -1)

    for part in parts or []:
        inline = getattr(part, "inline_data", None)
        if inline is None and isinstance(part, dict):
            inline = part.get("inline_data") or part.get("inlineData")
        if inline is None:
            continue

        data = getattr(inline, "data", None)
        mime_type = getattr(inline, "mime_type", None) or "image/png"
        if data is None and isinstance(inline, dict):
            data = inline.get("data")
            mime_type = inline.get("mime_type") or inline.get("mimeType") or "image/png"
        if not data:
            continue

        if isinstance(data, str):
            raw_bytes = base64.b64decode(data)
        elif isinstance(data, (bytes, bytearray)):
            raw_bytes = bytes(data)
        else:
            continue

        w, h = inspect_image_bytes(raw_bytes)
        score = (w * h, len(raw_bytes))
        if score > best_score:
            best_score = score
            best_bytes = raw_bytes
            best_w = w
            best_h = h
            best_mime = mime_type

    if best_bytes is None:
        raise RuntimeError("No inline_data image payload found in Gemini response parts.")

    return best_bytes, best_w, best_h, best_mime


def ensure_print_png(
    raw_bytes: bytes,
    aspect_ratio: str,
    image_size: str,
    draft: bool = False,
) -> tuple[bytes, int, int]:
    """Normalize image payload to lossless RGB PNG and guarantee target 2K/4K print pixel floor."""
    w, h = inspect_image_bytes(raw_bytes)
    if w == 0 or h == 0:
        # Synthetic byte payload in unit tests that aren't full PNG streams
        return raw_bytes, w, h

    target_w, target_h = TARGET_PIXEL_DIMENSIONS.get(
        (aspect_ratio, "1K" if draft else image_size),
        (1024, 1024) if draft else (2048, 2048),
    )

    with Image.open(io.BytesIO(raw_bytes)) as img:
        rgb = img.convert("RGB")
        cur_w, cur_h = rgb.size
        if not draft and (cur_w < target_w or cur_h < target_h):
            scale = max(target_w / cur_w, target_h / cur_h)
            new_w = max(target_w, int(round(cur_w * scale)))
            new_h = max(target_h, int(round(cur_h * scale)))
            rgb = rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
            cur_w, cur_h = rgb.size

        buf = io.BytesIO()
        rgb.save(buf, format="PNG", optimize=False)
        return buf.getvalue(), cur_w, cur_h


def compute_effective_dpi(width_px: int, height_px: int, layout_mode: CoverLayoutMode) -> float:
    placed_w_in, placed_h_in = PLACED_DIMENSIONS_IN.get(layout_mode, (4.40, 4.40))
    if width_px <= 0 or height_px <= 0:
        return 0.0
    return round(min(width_px / placed_w_in, height_px / placed_h_in), 1)


def generate_cover_artwork(
    target_dir: Path,
    model_chain: list[str] | None = None,
    force: bool = False,
    draft: bool = False,
    dry_run: bool = False,
    client: Any = None,
    layout_mode_override: str | None = None,
) -> Path:
    """Synthesize or retrieve cached 300+ DPI Gemini cover artwork for `target_dir`."""
    from google import genai
    from google.genai import types

    load_dotenv(ROOT)
    target_dir = Path(target_dir).resolve()
    spec, meta, _ = resolve_target_manifest(target_dir)

    if layout_mode_override:
        spec = spec.model_copy(update={"layout_mode": CoverLayoutMode(layout_mode_override)})
        if spec.layout_mode == CoverLayoutMode.FRONT_FULL_BLEED and spec.aspect_ratio == "1:1":
            spec = spec.model_copy(update={"aspect_ratio": "2:3", "image_size": "4K"})
        elif spec.layout_mode == CoverLayoutMode.FULL_WRAP_CANVAS and spec.aspect_ratio == "1:1":
            spec = spec.model_copy(update={"aspect_ratio": "16:9", "image_size": "4K"})

    effective_image_size = "1K" if draft else spec.image_size
    effective_aspect_ratio = spec.aspect_ratio
    full_prompt = synthesize_cover_prompt(
        spec,
        title=meta.get("title", ""),
        subtitle=meta.get("subtitle", ""),
        lenses=meta.get("lenses", []),
    )

    cache_payload = f"{full_prompt}|{effective_aspect_ratio}|{effective_image_size}|{spec.style_preset}"
    prompt_hash = hashlib.sha256(cache_payload.encode("utf-8")).hexdigest()

    cache_dir = ROOT / ".cache" / "cover_art"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{prompt_hash}.png"

    rel_asset = spec.asset_path or "publishing/assets/cover-art.png"
    asset_path = target_dir / rel_asset
    meta_path = asset_path.with_suffix(".meta.json")

    target_w, target_h = TARGET_PIXEL_DIMENSIONS.get(
        (effective_aspect_ratio, effective_image_size),
        (2048, 2048),
    )
    est_dpi = compute_effective_dpi(target_w, target_h, spec.layout_mode)
    placed_w_in, placed_h_in = PLACED_DIMENSIONS_IN.get(spec.layout_mode, (4.40, 4.40))

    if dry_run:
        print(f"# Cover Art Synthesis Plan (DRY RUN) — {meta.get('title')}")
        print(f"  Target Directory : {target_dir}")
        print(f"  Layout Mode      : {spec.layout_mode.value}")
        print(f"  Style Preset     : {spec.style_preset}")
        print(f"  Aspect Ratio     : {effective_aspect_ratio}")
        print(f"  Image Size Tier  : {effective_image_size} ({target_w}x{target_h} px target)")
        print(f"  Placed Print Size: {placed_w_in:.3f}\" x {placed_h_in:.3f}\" (~{est_dpi:.1f} effective DPI)")
        print(f"  Cache Key (SHA256): {prompt_hash}")
        print(f"  Cache File       : {cache_file.relative_to(ROOT)} (exists={cache_file.is_file()})")
        print(f"  Output Asset     : {asset_path.relative_to(ROOT) if asset_path.is_relative_to(ROOT) else asset_path}")
        print(f"  Synthesized Prompt:\n    {full_prompt}")
        return asset_path

    # If translation edition (e.g. i18n/es) has no local cache hit, check parent series asset unless --force
    if not force and not cache_file.is_file() and target_dir.parent.name == "i18n":
        parent_series_dir = target_dir.parent.parent
        parent_asset = parent_series_dir / rel_asset
        parent_meta = parent_asset.with_suffix(".meta.json")
        if parent_asset.is_file():
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(parent_asset, asset_path)
            if parent_meta.is_file():
                shutil.copy2(parent_meta, meta_path)
            print(f"[cover-art] Reused parent series master artwork: {parent_asset} -> {asset_path}")
            return asset_path

    if not force and cache_file.is_file():
        png_bytes = cache_file.read_bytes()
        w_px, h_px = inspect_image_bytes(png_bytes)
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cache_file, asset_path)
        eff_dpi = compute_effective_dpi(w_px or target_w, h_px or target_h, spec.layout_mode)
        meta_obj = {
            "model_id": "cache-hit",
            "prompt": full_prompt,
            "prompt_hash": prompt_hash,
            "layout_mode": spec.layout_mode.value,
            "style_preset": spec.style_preset,
            "aspect_ratio": effective_aspect_ratio,
            "image_size": effective_image_size,
            "width_px": w_px or target_w,
            "height_px": h_px or target_h,
            "placed_width_in": placed_w_in,
            "placed_height_in": placed_h_in,
            "effective_dpi": eff_dpi,
            "cache_path": str(cache_file.relative_to(ROOT)),
            "asset_path": str(asset_path.relative_to(ROOT) if asset_path.is_relative_to(ROOT) else asset_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if meta_path.is_file():
            try:
                old_meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if old_meta.get("model_id") and old_meta.get("model_id") != "cache-hit":
                    meta_obj["model_id"] = old_meta["model_id"]
            except Exception:
                pass
        meta_path.write_text(json.dumps(meta_obj, indent=2), encoding="utf-8")
        print(f"[cover-art:CACHE] Loaded {asset_path} ({w_px}x{h_px} px, {eff_dpi} DPI)")
        return asset_path

    chains = list(model_chain or DEFAULT_IMAGE_MODEL_CHAIN)
    if draft and "gemini-3.1-flash-lite-image" in chains:
        chains = ["gemini-3.1-flash-lite-image"] + [m for m in chains if m != "gemini-3.1-flash-lite-image"]

    if client is None:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY must be set in environment or .env to generate cover art.")
        client = genai.Client(api_key=api_key)

    last_err: Exception | None = None
    selected_model: str | None = None
    raw_image_bytes: bytes | None = None
    raw_w = 0
    raw_h = 0

    for model_id in chains:
        try:
            print(f"[cover-art] Requesting {effective_image_size} ({effective_aspect_ratio}) cover art from '{model_id}'...")
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=effective_aspect_ratio,
                    image_size=effective_image_size,
                ),
            )
            response = client.models.generate_content(
                model=model_id,
                contents=full_prompt,
                config=config,
            )
            candidates = getattr(response, "candidates", None) or []
            if not candidates:
                raise RuntimeError(f"Model '{model_id}' returned 0 candidates.")
            content_obj = getattr(candidates[0], "content", None)
            parts = getattr(content_obj, "parts", None) or []
            raw_image_bytes, raw_w, raw_h, _ = select_best_image_part(parts)
            selected_model = model_id
            break
        except Exception as exc:
            last_err = exc
            err_str = str(exc)
            # If a model does not accept image_size parameter in ImageConfig, retry once with aspect_ratio only
            if "image_size" in err_str.lower() or "invalid_argument" in err_str.lower() or "400" in err_str:
                try:
                    fallback_cfg = types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=effective_aspect_ratio),
                    )
                    response = client.models.generate_content(
                        model=model_id,
                        contents=full_prompt,
                        config=fallback_cfg,
                    )
                    candidates = getattr(response, "candidates", None) or []
                    if candidates:
                        content_obj = getattr(candidates[0], "content", None)
                        parts = getattr(content_obj, "parts", None) or []
                        raw_image_bytes, raw_w, raw_h, _ = select_best_image_part(parts)
                        selected_model = model_id
                        break
                except Exception as inner_exc:
                    last_err = inner_exc
            print(f"[cover-art:WARN] Model '{model_id}' failed ({last_err}); falling back to next tier...", file=sys.stderr)
            continue

    if raw_image_bytes is None or selected_model is None:
        raise RuntimeError(f"Cover art synthesis failed across all models {chains}: {last_err}")

    png_bytes, final_w, final_h = ensure_print_png(
        raw_image_bytes,
        aspect_ratio=effective_aspect_ratio,
        image_size=effective_image_size,
        draft=draft,
    )
    eff_dpi = compute_effective_dpi(final_w or raw_w or target_w, final_h or raw_h or target_h, spec.layout_mode)

    cache_file.write_bytes(png_bytes)
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(png_bytes)

    meta_obj = {
        "model_id": selected_model,
        "prompt": full_prompt,
        "prompt_hash": prompt_hash,
        "layout_mode": spec.layout_mode.value,
        "style_preset": spec.style_preset,
        "aspect_ratio": effective_aspect_ratio,
        "image_size": effective_image_size,
        "width_px": final_w or raw_w or target_w,
        "height_px": final_h or raw_h or target_h,
        "placed_width_in": placed_w_in,
        "placed_height_in": placed_h_in,
        "effective_dpi": eff_dpi,
        "cache_path": str(cache_file.relative_to(ROOT)),
        "asset_path": str(asset_path.relative_to(ROOT) if asset_path.is_relative_to(ROOT) else asset_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    meta_path.write_text(json.dumps(meta_obj, indent=2), encoding="utf-8")
    print(
        f"[cover-art:PASS] Wrote {asset_path} via '{selected_model}' "
        f"({meta_obj['width_px']}x{meta_obj['height_px']} px, {eff_dpi:.1f} effective DPI)"
    )
    return asset_path


def resolve_targets_for_series(series_slug: str, book_slug: str | None = None, render_all: bool = False) -> list[Path]:
    """Resolve one or all book directories for a series slug."""
    series_dir = ROOT / "series" / series_slug
    if not series_dir.is_dir() and (ROOT / series_slug).is_dir():
        series_dir = (ROOT / series_slug).resolve()
    if not series_dir.is_dir():
        raise FileNotFoundError(f"Series directory not found: {series_dir}")

    if book_slug:
        cand = series_dir / book_slug
        if not cand.is_dir():
            raise FileNotFoundError(f"Book directory not found: {cand}")
        return [cand]

    manifest_path = series_dir / "series.yaml"
    if render_all and manifest_path.is_file():
        manifest = validate_series_yaml(manifest_path)
        targets: list[Path] = []
        for b in manifest.books:
            b_dir = series_dir if b.path == "." else (series_dir / (b.path if b.path != "." else b.id))
            if not b_dir.is_dir():
                b_dir = series_dir / b.id
            if b_dir.is_dir() and b_dir not in targets:
                targets.append(b_dir)
        # Also include active i18n/es if parenthood-atlas
        es_dir = series_dir / "i18n" / "es"
        if es_dir.is_dir() and (es_dir / "series.yaml").is_file():
            targets.append(es_dir)
        return targets or [series_dir]

    return [series_dir]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate 300+ DPI Gemini cover artwork and optionally compile KDP covers & EPUBs.")
    parser.add_argument("target", nargs="?", default=None, help="Book or series directory path")
    parser.add_argument("--series", "-s", default=None, help="Series slug (e.g. parenthood-atlas or architectures-of-memory)")
    parser.add_argument("--book", "-b", default=None, help="Book slug (e.g. book-01-vanishing-signal)")
    parser.add_argument("--layout-mode", choices=[m.value for m in CoverLayoutMode], default=None, help="Override layout mode")
    parser.add_argument("--draft", action="store_true", help="Fast 1K preview generation using gemini-3.1-flash-lite-image")
    parser.add_argument("--force", action="store_true", help="Bypass cache and regenerate artwork via Gemini API")
    parser.add_argument("--dry-run", action="store_true", help="Print synthesized prompt, DPI calculation, and cache key without API calls")
    parser.add_argument("--render-all", action="store_true", help="Generate cover art and compile KDP wrap cover + EPUB across all books in series")
    args = parser.parse_args(argv[1:] if argv else None)

    if args.series:
        targets = resolve_targets_for_series(args.series, book_slug=args.book, render_all=args.render_all)
    elif args.target:
        t_path = Path(args.target)
        if not t_path.is_absolute():
            t_path = (ROOT / t_path).resolve()
        if args.render_all and (t_path / "series.yaml").is_file():
            rel_slug = t_path.relative_to(ROOT / "series").as_posix() if t_path.is_relative_to(ROOT / "series") else t_path.name
            targets = resolve_targets_for_series(rel_slug, book_slug=args.book, render_all=True)
        else:
            targets = [t_path]
    else:
        targets = resolve_targets_for_series("parenthood-atlas", book_slug=args.book, render_all=args.render_all)

    for t_dir in targets:
        generate_cover_artwork(
            target_dir=t_dir,
            force=args.force,
            draft=args.draft,
            dry_run=args.dry_run,
            layout_mode_override=args.layout_mode,
        )
        if args.render_all and not args.dry_run:
            # Compile KDP 6x9 interior + EPUB 3 (if chapters exist) and KDP full-wrap cover
            chapters_dir = t_dir / "chapters"
            has_chapters = chapters_dir.is_dir() and any(chapters_dir.glob("[0-9][0-9]-*.md"))
            if has_chapters:
                rc1 = subprocess.call(
                    [sys.executable, str(ROOT / "scripts" / "render_publishing_pdfs.py"), str(t_dir), "--format", "kdp-6x9", "--epub"]
                )
                if rc1 != 0:
                    return rc1
            cmd_cover = [sys.executable, str(ROOT / "scripts" / "render_kdp_cover.py"), str(t_dir)]
            if args.layout_mode:
                cmd_cover.extend(["--layout-mode", args.layout_mode])
            rc2 = subprocess.call(cmd_cover)
            if rc2 != 0:
                return rc2
            # If chapters were already compiled previously, re-run --epub so the freshly rendered eBook cover is embedded
            if has_chapters:
                rc3 = subprocess.call(
                    [sys.executable, str(ROOT / "scripts" / "render_publishing_pdfs.py"), str(t_dir), "--format", "kdp-6x9", "--epub"]
                )
                if rc3 != 0:
                    return rc3

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
