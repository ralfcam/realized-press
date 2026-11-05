#!/usr/bin/env python3
"""Amazon KDP Full Wrap Cover Generator & Hybrid Raster + Vector Compositor (`ARC-64` / `ARC-98`, `BWE v1.1.0`).

Computes exact KDP paperback cover specifications:
- Trim: 6" x 9" (152.4 mm x 228.6 mm)
- Bleed: 0.125" (3.175 mm) on all 4 edges
- Spine width: page_count * paper_thickness (Standard White: 0.002252 in / 0.0572 mm)
- Total Cover Dimensions:
    Width = Bleed + Back + Spine + Front + Bleed
    Height = Bleed + Trim Height + Bleed
- Safe margins: 0.25" (6.35 mm) inside trim lines
- Barcode safe locus: 2" x 1.2" (50.8 mm x 30.48 mm) on lower right back cover

Supports four composable `CoverLayoutMode` modes:
- `vector_only`: Pure programmatic vector cover
- `front_hero_vignette` (Default): 4.40" x 4.40" (111.76 mm x 111.76 mm) Gemini 2K/4K raster vignette (>465 DPI)
- `front_full_bleed`: 6.125" x 9.250" front full-bleed Gemini 4K panel (>445 DPI) + solid vector spine/back
- `full_wrap_canvas`: Continuous 16:9 4K panoramic wrap (>433 DPI) + translucent vector reading scrims (opacity=0.82)
"""

from __future__ import annotations

import argparse
import shutil
import sys
import textwrap
from pathlib import Path
from typing import Any

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from bwe.schema import CoverArtSpec, CoverLayoutMode
from render_publishing_pdfs import resolve_serif_fonts

# Paper constants (Amazon KDP specifications)
WHITE_PAPER_THICKNESS_IN = 0.002252  # inches per page
CREAM_PAPER_THICKNESS_IN = 0.002500  # inches per page
BLEED_IN = 0.125
TRIM_WIDTH_IN = 6.0
TRIM_HEIGHT_IN = 9.0
IN_TO_MM = 25.4
MIN_SPINE_TEXT_PAGES = 79  # Amazon KDP threshold: spine text rejected if < 79 pages

ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def hex_to_rgb(hex_str: str, fallback: tuple[int, int, int] = (15, 23, 42)) -> tuple[int, int, int]:
    s = (hex_str or "").strip().lstrip("#")
    if len(s) == 6:
        try:
            return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        except ValueError:
            pass
    return fallback


def calculate_dimensions(page_count: int, paper_type: str = "white") -> dict[str, float]:
    thickness = WHITE_PAPER_THICKNESS_IN if paper_type == "white" else CREAM_PAPER_THICKNESS_IN
    spine_in = page_count * thickness
    width_in = BLEED_IN + TRIM_WIDTH_IN + spine_in + TRIM_WIDTH_IN + BLEED_IN
    height_in = BLEED_IN + TRIM_HEIGHT_IN + BLEED_IN

    return {
        "page_count": page_count,
        "spine_in": spine_in,
        "spine_mm": spine_in * IN_TO_MM,
        "width_in": width_in,
        "width_mm": width_in * IN_TO_MM,
        "height_in": height_in,
        "height_mm": height_in * IN_TO_MM,
        "bleed_mm": BLEED_IN * IN_TO_MM,
        "trim_w_mm": TRIM_WIDTH_IN * IN_TO_MM,
        "trim_h_mm": TRIM_HEIGHT_IN * IN_TO_MM,
        "back_x_mm": BLEED_IN * IN_TO_MM,
        "spine_x_mm": (BLEED_IN + TRIM_WIDTH_IN) * IN_TO_MM,
        "front_x_mm": (BLEED_IN + TRIM_WIDTH_IN + spine_in) * IN_TO_MM,
    }


def resolve_cover_asset_path(book_dir: Path, explicit_art_path: Path | None = None, rel_asset: str = "publishing/assets/cover-art.png") -> Path | None:
    """Resolve cover-art.png for book_dir, falling back to parent series artwork for i18n/<lang> editions."""
    if explicit_art_path is not None:
        return explicit_art_path if explicit_art_path.is_file() else None

    local_asset = book_dir / rel_asset
    if local_asset.is_file():
        return local_asset

    # Automatic i18n/<lang> fallback to parent series master illustration
    if book_dir.parent.name == "i18n":
        parent_series_dir = book_dir.parent.parent
        parent_asset = parent_series_dir / rel_asset
        if parent_asset.is_file():
            local_asset.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(parent_asset, local_asset)
            parent_meta = parent_asset.with_suffix(".meta.json")
            if parent_meta.is_file():
                shutil.copy2(parent_meta, local_asset.with_suffix(".meta.json"))
            return local_asset

    return None


def export_ebook_front_cover(
    title: str,
    subtitle: str,
    author: str,
    series_header: str,
    badge_txt: str,
    art_path: Path | None,
    output_png: Path,
    fonts: dict[str, Path] | None = None,
    cover_spec: CoverArtSpec | None = None,
) -> Path:
    """Render a standalone 1600x2400 px Kindle / EPUB 3 front cover image (PNG + JPG)."""
    spec = cover_spec or CoverArtSpec()
    bg_rgb = hex_to_rgb(spec.palette_bg_hex, (17, 24, 39))
    accent_rgb = hex_to_rgb(spec.palette_accent_hex, (201, 158, 92))
    text_rgb = hex_to_rgb(spec.palette_text_hex, (249, 250, 251))

    W, H = 1600, 2400
    canvas = Image.new("RGB", (W, H), bg_rgb)

    if art_path and art_path.is_file() and spec.layout_mode != CoverLayoutMode.VECTOR_ONLY:
        try:
            with Image.open(art_path) as art_img:
                art_rgb = art_img.convert("RGB")
                if spec.layout_mode in (CoverLayoutMode.FRONT_FULL_BLEED, CoverLayoutMode.FULL_WRAP_CANVAS):
                    # Crop right-hand front panel if full_wrap_canvas, else fit to 1600x2400
                    if spec.layout_mode == CoverLayoutMode.FULL_WRAP_CANVAS:
                        aw, ah = art_rgb.size
                        art_rgb = art_rgb.crop((int(aw * 0.52), 0, aw, ah))
                    art_resized = art_rgb.resize((W, H), Image.Resampling.LANCZOS)
                    canvas.paste(art_resized, (0, 0))
                    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    odraw = ImageDraw.Draw(overlay)
                    odraw.rectangle([0, 0, W, int(H * 0.34)], fill=(*bg_rgb, 195))
                    odraw.rectangle([0, int(H * 0.80), W, H], fill=(*bg_rgb, 205))
                    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
                else:
                    # Front hero vignette (centered 1140x1140 square frame)
                    hero_px = 1140
                    hx = (W - hero_px) // 2
                    hy = 790
                    art_resized = art_rgb.resize((hero_px, hero_px), Image.Resampling.LANCZOS)
                    canvas.paste(art_resized, (hx, hy))
                    draw_frame = ImageDraw.Draw(canvas)
                    draw_frame.rectangle([hx - 6, hy - 6, hx + hero_px + 6, hy + hero_px + 6], outline=accent_rgb, width=4)
        except Exception:
            pass

    draw = ImageDraw.Draw(canvas)
    # Outer decorative frame
    draw.rectangle([56, 56, W - 56, H - 56], outline=accent_rgb, width=5)
    draw.rectangle([72, 72, W - 72, H - 72], outline=accent_rgb, width=2)

    regular_ttf = str(fonts.get("", "")) if fonts else ""
    bold_ttf = str(fonts.get("B", regular_ttf)) if fonts else ""
    italic_ttf = str(fonts.get("I", regular_ttf)) if fonts else ""

    def load_pil_font(path_str: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if path_str and Path(path_str).is_file():
            try:
                return ImageFont.truetype(path_str, size=size)
            except Exception:
                pass
        return ImageFont.load_default()

    font_hdr = load_pil_font(bold_ttf, 32)
    font_title = load_pil_font(bold_ttf, 74)
    font_sub = load_pil_font(italic_ttf, 36)
    font_author = load_pil_font(bold_ttf, 46)
    font_colophon = load_pil_font(regular_ttf, 28)

    def draw_centered_lines(lines: list[str], start_y: int, font: Any, fill: tuple[int, int, int], line_step: int) -> int:
        y = start_y
        for ln in lines:
            bbox = draw.textbbox((0, 0), ln, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, y), ln, font=font, fill=fill)
            y += line_step
        return y

    draw_centered_lines([series_header], 145, font_hdr, accent_rgb, 46)
    title_lines = textwrap.wrap(title.upper(), width=26)[:3]
    curr_y = draw_centered_lines(title_lines, 230, font_title, text_rgb, 88)
    draw.line([(W // 2 - 180, curr_y + 18), (W // 2 + 180, curr_y + 18)], fill=accent_rgb, width=3)
    sub_lines = textwrap.wrap(subtitle, width=54)[:3]
    draw_centered_lines(sub_lines, curr_y + 44, font_sub, (226, 232, 240), 48)

    draw_centered_lines([author], 2100, font_author, text_rgb, 60)
    draw_centered_lines(["OPEN KNOWLEDGE FORMAT (OKF v0.3)"], 2185, font_colophon, accent_rgb, 40)

    output_png.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_png, format="PNG")
    output_jpg = output_png.with_suffix(".jpg")
    canvas.save(output_jpg, format="JPEG", quality=94)
    return output_png


def render_kdp_cover(
    title: str,
    subtitle: str,
    author: str,
    blurb_paragraphs: list[str],
    dims: dict[str, float],
    output_pdf: Path,
    fonts: dict[str, Path] | None = None,
    publishing_copy: dict | None = None,
    cover_spec: CoverArtSpec | None = None,
    art_path: Path | None = None,
    layout_mode_override: str | None = None,
    force_spine_text: bool = False,
) -> None:
    spec = cover_spec or CoverArtSpec()
    if layout_mode_override:
        spec = spec.model_copy(update={"layout_mode": CoverLayoutMode(layout_mode_override)})

    layout_mode = spec.layout_mode
    has_art = art_path is not None and art_path.is_file() and layout_mode != CoverLayoutMode.VECTOR_ONLY

    bg_r, bg_g, bg_b = hex_to_rgb(spec.palette_bg_hex, (15, 23, 42))
    acc_r, acc_g, acc_b = hex_to_rgb(spec.palette_accent_hex, (201, 158, 92))
    txt_r, txt_g, txt_b = hex_to_rgb(spec.palette_text_hex, (255, 255, 255))

    pdf = FPDF(unit="mm", format=(dims["width_mm"], dims["height_mm"]))
    pdf.set_auto_page_break(False)
    pdf.add_page()

    copy = publishing_copy or {}
    series_hdr = copy.get("series_header", "REALIZED PRESS  |  VOLUME I")
    badge_txt = copy.get(
        "badge",
        "15 Curated Chapters   |   78 Evidence Cards\nSystematically Calibrated Developmental Science",
    )
    category_txt = copy.get("category_line", "NONFICTION  /  DEVELOPMENTAL SCIENCE  /  PARENTING")
    back_title_txt = copy.get("back_title", "A Natural-History Atlas of the First 1,000 Days")
    feat_hdr = copy.get("features_header", "KEY EPISTEMIC ATTRIBUTES:")
    features = copy.get(
        "features",
        [
            "- 15 curated developmental chapters from preconception through age three.",
            "- Calibrated claim verbs strictly matching underlying evidence certainty grades.",
            "- Systematic genetically informed (GI) confounding audits across all 78 cards.",
            "- Governed by Open Knowledge Format (OKF v0.3) and verified DOIs.",
        ],
    )
    colophon_txt = copy.get("colophon", "Monorepo Book Writing Environment (BWE)")

    # Font setup
    font_family = "Serif"
    if fonts:
        for style, fpath in fonts.items():
            pdf.add_font(font_family, style=style, fname=str(fpath))
    else:
        font_family = "Helvetica"

    # Base Background Fill across entire wrap canvas
    pdf.set_fill_color(bg_r, bg_g, bg_b)
    pdf.rect(0, 0, dims["width_mm"], dims["height_mm"], style="F")

    fx = dims["front_x_mm"]
    fw = dims["trim_w_mm"]
    fh = dims["trim_h_mm"]
    by = dims["bleed_mm"]
    sx = dims["spine_x_mm"]
    sw = dims["spine_mm"]
    bx = dims["back_x_mm"]
    bw = dims["trim_w_mm"]

    # ---------------- RASTER ARTWORK LAYER COMPOSITING ----------------
    if has_art and art_path is not None:
        if layout_mode == CoverLayoutMode.FULL_WRAP_CANVAS:
            # 16:9 4K continuous panoramic wrap spanning full width x height
            pdf.image(str(art_path), x=0, y=0, w=dims["width_mm"], h=dims["height_mm"])
            # Reading scrims over back-cover blurb zone, spine, and front typography header/footer
            with pdf.local_context(fill_opacity=0.82):
                pdf.set_fill_color(bg_r, bg_g, bg_b)
                pdf.rect(bx + 8, by + 10, bw - 16, fh - 20, style="F")
                pdf.rect(sx, 0, sw, dims["height_mm"], style="F")
                pdf.rect(fx + 8, by + 10, fw - 16, 62, style="F")
                pdf.rect(fx + 8, by + 182, fw - 16, 38, style="F")
        elif layout_mode == CoverLayoutMode.FRONT_FULL_BLEED:
            # 2:3 4K front full-bleed panel covering front trim + right/top/bottom bleed (6.125" x 9.250")
            front_bleed_w = fw + dims["bleed_mm"]
            pdf.image(str(art_path), x=fx, y=0, w=front_bleed_w, h=dims["height_mm"])
            with pdf.local_context(fill_opacity=0.76):
                pdf.set_fill_color(bg_r, bg_g, bg_b)
                pdf.rect(fx + 8, by + 10, fw - 16, 62, style="F")
                pdf.rect(fx + 8, by + 182, fw - 16, 38, style="F")
        else:
            # Default: front_hero_vignette — 4.40" x 4.40" (111.76 mm x 111.76 mm) hero frame (~465.5 DPI at 2K)
            hero_w_mm = 4.40 * IN_TO_MM  # 111.76 mm
            hero_h_mm = 4.40 * IN_TO_MM  # 111.76 mm
            hero_x_mm = fx + (fw - hero_w_mm) / 2.0
            hero_y_mm = by + 74.0
            pdf.image(str(art_path), x=hero_x_mm, y=hero_y_mm, w=hero_w_mm, h=hero_h_mm)
            pdf.set_draw_color(acc_r, acc_g, acc_b)
            pdf.set_line_width(0.45)
            pdf.rect(hero_x_mm - 1.2, hero_y_mm - 1.2, hero_w_mm + 2.4, hero_h_mm + 2.4)

    # Front cover outer decorative frame
    pdf.set_draw_color(acc_r, acc_g, acc_b)
    pdf.set_line_width(0.6)
    pdf.rect(fx + 8, by + 8, fw - 16, fh - 16)
    pdf.set_line_width(0.2)
    pdf.rect(fx + 10, by + 10, fw - 20, fh - 20)

    # ---------------- FRONT COVER VECTOR TYPOGRAPHY ----------------
    if has_art:
        # Compact header layout preserving generous breathing room around the 4.40"x4.40" hero frame
        pdf.set_xy(fx + 14, by + 15)
        pdf.set_text_color(acc_r, acc_g, acc_b)
        pdf.set_font(font_family, "B", 9.5)
        pdf.cell(fw - 28, 5, series_hdr, align="C", new_x="LMARGIN", new_y="NEXT")

        title_pt = 21 if len(title) <= 26 else 18.5
        pdf.set_xy(fx + 14, by + 23)
        pdf.set_text_color(txt_r, txt_g, txt_b)
        pdf.set_font(font_family, "B", title_pt)
        pdf.multi_cell(fw - 28, 8.8, title.upper(), align="C")

        curr_y = pdf.get_y() + 2.0
        pdf.set_draw_color(acc_r, acc_g, acc_b)
        pdf.line(fx + fw / 2 - 24, curr_y, fx + fw / 2 + 24, curr_y)

        pdf.set_xy(fx + 14, curr_y + 3.0)
        pdf.set_text_color(226, 232, 240)
        pdf.set_font(font_family, "I", 10.0)
        pdf.multi_cell(fw - 28, 5.2, subtitle, align="C")

        # Footer zone below hero vignette (hero ends at by + 185.76 mm)
        pdf.set_xy(fx + 14, by + 189.0)
        pdf.set_text_color(148, 163, 184)
        pdf.set_font(font_family, "", 8.0)
        pdf.multi_cell(fw - 28, 4.4, badge_txt, align="C")

        pdf.set_xy(fx + 14, by + 201.5)
        pdf.set_text_color(txt_r, txt_g, txt_b)
        pdf.set_font(font_family, "B", 13.5)
        pdf.cell(fw - 28, 7, author, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_xy(fx + 14, by + 210.0)
        pdf.set_text_color(acc_r, acc_g, acc_b)
        pdf.set_font(font_family, "", 8.5)
        pdf.cell(fw - 28, 4.5, "OPEN KNOWLEDGE FORMAT (OKF v0.3)", align="C")
    else:
        # Pure vector cover layout
        pdf.set_xy(fx + 15, by + 22)
        pdf.set_text_color(acc_r, acc_g, acc_b)
        pdf.set_font(font_family, "B", 10)
        pdf.cell(fw - 30, 6, series_hdr, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_xy(fx + 15, by + 45)
        pdf.set_text_color(txt_r, txt_g, txt_b)
        pdf.set_font(font_family, "B", 24)
        pdf.multi_cell(fw - 30, 11, title.upper(), align="C")

        curr_y = pdf.get_y() + 4
        pdf.set_draw_color(acc_r, acc_g, acc_b)
        pdf.line(fx + fw / 2 - 25, curr_y, fx + fw / 2 + 25, curr_y)

        pdf.set_xy(fx + 15, curr_y + 8)
        pdf.set_text_color(226, 232, 240)
        pdf.set_font(font_family, "I", 11)
        pdf.multi_cell(fw - 30, 6.5, subtitle, align="C")

        pdf.set_xy(fx + 15, by + 145)
        pdf.set_text_color(148, 163, 184)
        pdf.set_font(font_family, "", 9)
        pdf.multi_cell(fw - 30, 5.5, badge_txt, align="C")

        pdf.set_xy(fx + 15, by + 185)
        pdf.set_text_color(txt_r, txt_g, txt_b)
        pdf.set_font(font_family, "B", 14)
        pdf.cell(fw - 30, 8, author, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_xy(fx + 15, by + 195)
        pdf.set_text_color(acc_r, acc_g, acc_b)
        pdf.set_font(font_family, "", 9)
        pdf.cell(fw - 30, 5, "OPEN KNOWLEDGE FORMAT (OKF v0.3)", align="C")

    # ---------------- SPINE ----------------
    # Amazon KDP allows spine text only on volumes with >= 79 pages.
    # On slim volumes (< 79 pages), text must be omitted to preserve KDP's 0.0625" (1.59 mm) hinge margin.
    has_spine_text = (int(dims.get("page_count", 0)) >= MIN_SPINE_TEXT_PAGES) or force_spine_text

    # Draw spine border lines
    pdf.set_draw_color(30, 41, 59)
    pdf.line(sx, 0, sx, dims["height_mm"])
    pdf.line(sx + sw, 0, sx + sw, dims["height_mm"])

    if has_spine_text:
        with pdf.rotation(270, sx + sw / 2, by + fh / 2):
            pdf.set_text_color(txt_r, txt_g, txt_b)
            pdf.set_font(font_family, "B", 9)
            pdf.set_xy(sx + sw / 2 - 80, by + fh / 2 - 3.5)
            spine_text = f"{title.upper()}    -    {author}    -    REALIZED PRESS"
            pdf.cell(160, 7, spine_text, align="C")

    # ---------------- BACK COVER ----------------
    pdf.set_xy(bx + 15, by + 20)
    pdf.set_text_color(acc_r, acc_g, acc_b)
    pdf.set_font(font_family, "B", 8.5)
    pdf.cell(bw - 30, 5, category_txt, align="L")

    pdf.set_xy(bx + 15, by + 30)
    pdf.set_text_color(txt_r, txt_g, txt_b)
    pdf.set_font(font_family, "B", 13)
    pdf.multi_cell(bw - 30, 6.5, back_title_txt, align="L")

    pdf.set_text_color(226, 232, 240)
    pdf.set_font(font_family, "", 8.5)
    curr_by = max(by + 40, pdf.get_y() + 3)
    for para in blurb_paragraphs:
        pdf.set_xy(bx + 15, curr_by)
        pdf.multi_cell(bw - 30, 4.8, para, align="L")
        curr_by = pdf.get_y() + 3

    pdf.set_xy(bx + 15, curr_by + 2)
    pdf.set_text_color(acc_r, acc_g, acc_b)
    pdf.set_font(font_family, "B", 8.5)
    pdf.cell(bw - 30, 5, feat_hdr, align="L")

    curr_by = pdf.get_y() + 6
    pdf.set_text_color(203, 213, 225)
    pdf.set_font(font_family, "", 8)
    for feat in features:
        pdf.set_xy(bx + 18, curr_by)
        pdf.cell(bw - 36, 4.5, feat, align="L")
        curr_by += 4.5

    # Mandatory opaque white ISBN Barcode Reserve Box (50.8 mm x 30.48 mm = 2.0" x 1.2")
    barcode_w = 50.8
    barcode_h = 30.48
    barcode_x = bx + bw - barcode_w - 15
    barcode_y = by + fh - barcode_h - 15

    with pdf.local_context(fill_opacity=1.0):
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(148, 163, 184)
        pdf.rect(barcode_x, barcode_y, barcode_w, barcode_h, style="FD")

        pdf.set_xy(barcode_x, barcode_y + 10)
        pdf.set_text_color(71, 85, 105)
        pdf.set_font(font_family, "", 7)
        pdf.cell(barcode_w, 4, "ISBN / EAN BARCODE", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_xy(barcode_x, barcode_y + 15)
        pdf.cell(barcode_w, 4, 'KDP Safe Zone (2.0" x 1.2")', align="C")

    # Colophon left of barcode
    pdf.set_xy(bx + 15, barcode_y + 5)
    pdf.set_text_color(148, 163, 184)
    pdf.set_font(font_family, "", 8)
    pdf.cell(bw - barcode_w - 35, 4.5, "REALIZED PRESS", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(bx + 15, barcode_y + 10)
    pdf.set_font(font_family, "I", 7.5)
    pdf.cell(bw - barcode_w - 35, 4, "https://github.com/ralfcam/realized-press", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(bx + 15, barcode_y + 15)
    pdf.cell(bw - barcode_w - 35, 4, colophon_txt, align="L")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_pdf))

    # Also export standalone 1600x2400 eBook front cover asset for EPUB 3 & Web Reader sync
    ebook_png = output_pdf.parent / "assets" / "front-cover-ebook.png"
    export_ebook_front_cover(
        title=title,
        subtitle=subtitle,
        author=author,
        series_header=series_hdr,
        badge_txt=badge_txt,
        art_path=art_path if has_art else None,
        output_png=ebook_png,
        fonts=fonts,
        cover_spec=spec,
    )


def resolve_book_metadata_and_spec(book_dir: Path) -> tuple[str, str, str, list[str], dict[str, Any] | None, CoverArtSpec]:
    """Load title, subtitle, author, blurb, publishing_copy, and CoverArtSpec for book_dir."""
    title = "Parenthood: The Atlas"
    subtitle = "What Science Knows, What It Doesn't, and Where Art Begins from Conception to Age Three"
    author = "Jose Campos"
    blurb = [
        "Parenthood: The Atlas is a longitudinal evidence atlas of developmental science from roughly one year before conception through age three. It distinguishes three non-collapsible domains: what science can observe, what interpretation suggests, and what the relational art of caregiving demands.",
        "Rather than prescriptive parenting manuals or single-study alarmism, this work presents a systematic natural-history map across fifteen curated developmental milestones. Every claim is calibrated to verified empirical certainty grades under the Open Knowledge Format.",
        "From the placental filtration of maternal cortisol to the emergence of communicative turns, from neonatal transition physiology to the fragile mechanics of toddler self-regulation, The Atlas offers parents and practitioners an unpadded, evidence-anchored foundation.",
    ]
    publishing_copy: dict[str, Any] | None = None
    cover_spec = CoverArtSpec()

    manifest_file = (
        book_dir / "series.yaml"
        if (book_dir / "series.yaml").is_file()
        else (book_dir.parent / "series.yaml" if (book_dir.parent / "series.yaml").is_file() else None)
    )
    if manifest_file and manifest_file.is_file():
        try:
            import yaml
            manifest = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
            title = manifest.get("title", title)
            subtitle = manifest.get("subtitle", subtitle)
            author = manifest.get("author", author)
            publishing_copy = dict(manifest.get("publishing_copy") or {})
            if "cover_art" in manifest and isinstance(manifest["cover_art"], dict):
                cover_spec = CoverArtSpec.model_validate(manifest["cover_art"])

            # Check if book_dir is one of the volumes in `books:`
            books_list = manifest.get("books") or []
            for idx, b in enumerate(books_list):
                if not isinstance(b, dict):
                    continue
                b_id = b.get("id", "")
                b_path = b.get("path", ".")
                if b_id == book_dir.name or b_path == book_dir.name or (b_path == "." and manifest_file.parent == book_dir):
                    if len(books_list) > 1:
                        title = b.get("title", title)
                        subtitle = b.get("subtitle", subtitle)
                        roman = ROMAN_NUMERALS[idx] if idx < len(ROMAN_NUMERALS) else str(idx + 1)
                        series_title_upper = manifest.get("title", "REALIZED PRESS").upper()
                        publishing_copy.setdefault("series_header", f"{series_title_upper}  |  BOOK {roman}")
                        publishing_copy.setdefault(
                            "badge",
                            "Technical  |  Organizational  |  Philosophical\nCalibrated under the Open Knowledge Format (OKF v0.3)",
                        )
                        publishing_copy.setdefault(
                            "category_line",
                            "NONFICTION  /  ARTIFICIAL INTELLIGENCE  /  PHILOSOPHY OF MIND",
                        )
                        publishing_copy.setdefault("back_title", f"{title}: {subtitle}")
                        publishing_copy.setdefault(
                            "features",
                            [
                                "- Three-Lens architecture: Technical mechanisms, Organizational systems, Philosophical stakes.",
                                "- Calibrated claim verbs matching underlying OKF v0.3 evidence card certainty grades.",
                                "- Verified primary DOIs with zero retractions across machine learning and cognitive science.",
                                "- Part of the five-volume series The Architectures of Memory.",
                            ],
                        )
                        blurb = [
                            f"{title} ({subtitle}) is Book {roman} of The Architectures of Memory, a five-volume investigation into how artificial networks, human institutions, and philosophical traditions encode, retrieve, and forget.",
                            "Every chapter moves through three non-collapsible lenses: exact mathematical and architectural derivations, organizational failure modes across engineering teams, and the philosophical stakes of memory and identity.",
                            "Governed by the Open Knowledge Format (OKF v0.3), every empirical claim is anchored to verified primary literature and calibrated to its replication and certainty grade.",
                        ]
                    if "cover_art" in b and isinstance(b["cover_art"], dict):
                        cover_spec = CoverArtSpec.model_validate(b["cover_art"])
                    break

            if publishing_copy and "blurb" in publishing_copy:
                blurb = publishing_copy["blurb"]
        except Exception:
            pass

    return title, subtitle, author, blurb, publishing_copy, cover_spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Render Amazon KDP 6"x9" wrap cover PDF with Hybrid Raster + Vector Compositing.')
    parser.add_argument("book", default="series/parenthood-atlas", nargs="?", help="Series or book directory")
    parser.add_argument("--pages", type=int, default=None, help="Interior page count (defaults to inspecting interior PDF)")
    parser.add_argument("--paper", choices=["white", "cream"], default="white", help="Paper type (white=0.002252in, cream=0.0025in)")
    parser.add_argument("--generate-art", action="store_true", help="Synthesize or refresh Gemini cover art before compositing")
    parser.add_argument(
        "--layout-mode",
        choices=[m.value for m in CoverLayoutMode],
        default=None,
        help="Override cover layout mode (vector_only, front_hero_vignette, front_full_bleed, full_wrap_canvas)",
    )
    parser.add_argument("--art-path", type=Path, default=None, help="Explicit path to raster cover artwork PNG")
    parser.add_argument("--draft", action="store_true", help="Use fast 1K preview tier when --generate-art is active")
    parser.add_argument("--force-art", action="store_true", help="Force regeneration of Gemini cover art when --generate-art is active")
    parser.add_argument("--force-spine-text", action="store_true", help="Force spine text even if page count < 79 pages")
    parser.add_argument("--output", type=Path, default=None, help="Explicit output path for the cover wrap PDF")
    args = parser.parse_args(argv[1:] if argv else None)

    book_dir = Path(args.book).resolve()
    pub_dir = book_dir / "publishing"

    if args.generate_art:
        from generate_cover_art import generate_cover_artwork
        generate_cover_artwork(
            target_dir=book_dir,
            force=args.force_art,
            draft=args.draft,
            layout_mode_override=args.layout_mode,
        )

    base_name = book_dir.parent.parent.name if book_dir.parent.name == "i18n" else book_dir.name
    interior_pdf = (
        pub_dir / f"{base_name}-kdp-6x9.pdf"
        if (pub_dir / f"{base_name}-kdp-6x9.pdf").is_file()
        else pub_dir / f"{book_dir.name}-kdp-6x9.pdf"
    )

    page_count = args.pages
    if page_count is None:
        if interior_pdf.is_file():
            reader = PdfReader(str(interior_pdf))
            page_count = len(reader.pages)
            print(f"[kdp-cover] Detected {page_count} pages from {interior_pdf.name}")
        else:
            page_count = 152
            print(f"[kdp-cover] Interior PDF not found, defaulting to {page_count} pages")

    dims = calculate_dimensions(page_count, args.paper)
    suffix = "-cream" if args.paper == "cream" else ""
    if args.output:
        output_pdf = args.output.resolve()
    else:
        cover_filename = (
            f"{base_name}-kdp-cover{suffix}.pdf"
            if base_name != book_dir.name
            else f"{book_dir.name}-kdp-cover{suffix}.pdf"
        )
        output_pdf = pub_dir / cover_filename
    fonts = resolve_serif_fonts()

    title, subtitle, author, blurb, publishing_copy, cover_spec = resolve_book_metadata_and_spec(book_dir)
    if args.layout_mode:
        cover_spec = cover_spec.model_copy(update={"layout_mode": CoverLayoutMode(args.layout_mode)})

    art_path = resolve_cover_asset_path(
        book_dir=book_dir,
        explicit_art_path=args.art_path,
        rel_asset=cover_spec.asset_path or "publishing/assets/cover-art.png",
    )

    render_kdp_cover(
        title=title,
        subtitle=subtitle,
        author=author,
        blurb_paragraphs=blurb,
        dims=dims,
        output_pdf=output_pdf,
        fonts=fonts,
        publishing_copy=publishing_copy,
        cover_spec=cover_spec,
        art_path=art_path,
        layout_mode_override=args.layout_mode,
        force_spine_text=args.force_spine_text,
    )

    has_spine = (int(dims.get("page_count", 0)) >= MIN_SPINE_TEXT_PAGES) or args.force_spine_text
    rel_out = output_pdf.relative_to(ROOT) if output_pdf.is_relative_to(ROOT) else output_pdf
    print(f"[kdp-cover:PASS] Wrote {rel_out} ({output_pdf.stat().st_size:,} bytes)")
    print(f"  Layout mode: {cover_spec.layout_mode.value} (art={'embedded: ' + art_path.name if art_path else 'vector-only'})")
    print(f"  Spine width: {dims['spine_in']:.4f}\" ({dims['spine_mm']:.2f} mm) — text: {'included' if has_spine else 'omitted (pages < 79)'}")
    print(f"  Total cover size: {dims['width_in']:.4f}\" x {dims['height_in']:.4f}\" ({dims['width_mm']:.2f} x {dims['height_mm']:.2f} mm)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
