#!/usr/bin/env python3
"""Amazon KDP Full Wrap Cover Generator (6"x9" Trade Paperback).

Computes exact KDP paperback cover specifications:
- Trim: 6" x 9" (152.4 mm x 228.6 mm)
- Bleed: 0.125" (3.175 mm) on all 4 edges
- Spine width: page_count * paper_thickness (Standard White: 0.002252 in / 0.0572 mm)
- Total Cover Dimensions:
    Width = Bleed + Back + Spine + Front + Bleed
    Height = Bleed + Trim Height + Bleed
- Safe margins: 0.25" (6.35 mm) inside trim lines
- Barcode safe locus: 2" x 1.2" (50.8 mm x 30.5 mm) on lower right back cover
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fpdf import FPDF
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from render_publishing_pdfs import resolve_serif_fonts

# Paper constants (Amazon KDP specifications)
WHITE_PAPER_THICKNESS_IN = 0.002252  # inches per page
CREAM_PAPER_THICKNESS_IN = 0.002500  # inches per page
BLEED_IN = 0.125
TRIM_WIDTH_IN = 6.0
TRIM_HEIGHT_IN = 9.0
IN_TO_MM = 25.4


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


def render_kdp_cover(
    title: str,
    subtitle: str,
    author: str,
    blurb_paragraphs: list[str],
    dims: dict[str, float],
    output_pdf: Path,
    fonts: dict[str, Path] | None = None,
    publishing_copy: dict | None = None,
) -> None:
    pdf = FPDF(unit="mm", format=(dims["width_mm"], dims["height_mm"]))
    pdf.set_auto_page_break(False)
    pdf.add_page()

    copy = publishing_copy or {}
    series_hdr = copy.get("series_header", "REALIZED PRESS  |  VOLUME I")
    badge_txt = copy.get("badge", "15 Curated Chapters   |   77 Evidence Cards\nSystematically Calibrated Developmental Science")
    category_txt = copy.get("category_line", "NONFICTION  /  DEVELOPMENTAL SCIENCE  /  PARENTING")
    back_title_txt = copy.get("back_title", "A Natural-History Atlas of the First 1,000 Days")
    feat_hdr = copy.get("features_header", "KEY EPISTEMIC ATTRIBUTES:")
    features = copy.get("features", [
        "- 15 curated developmental chapters from preconception through age three.",
        "- Calibrated claim verbs strictly matching underlying evidence certainty grades.",
        "- Systematic genetically informed (GI) confounding audits across all 77 cards.",
        "- Governed by Open Knowledge Format (OKF v0.2) and verified DOIs.",
    ])
    colophon_txt = copy.get("colophon", "Monorepo Book Writing Environment (BWE)")

    # Font setup
    font_family = "Serif"
    if fonts:
        for style, fpath in fonts.items():
            pdf.add_font(font_family, style=style, fname=str(fpath))
    else:
        font_family = "Helvetica"

    # Background: Sophisticated deep midnight slate (#0F172A)
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, dims["width_mm"], dims["height_mm"], style="F")

    # Front cover decorative frame
    fx = dims["front_x_mm"]
    fw = dims["trim_w_mm"]
    fh = dims["trim_h_mm"]
    by = dims["bleed_mm"]

    pdf.set_draw_color(201, 158, 92)  # Muted gold (#C99E5C)
    pdf.set_line_width(0.6)
    pdf.rect(fx + 8, by + 8, fw - 16, fh - 16)
    pdf.set_line_width(0.2)
    pdf.rect(fx + 10, by + 10, fw - 20, fh - 20)

    # ---------------- FRONT COVER ----------------
    # Series Header
    pdf.set_xy(fx + 15, by + 22)
    pdf.set_text_color(201, 158, 92)
    pdf.set_font(font_family, "B", 10)
    pdf.cell(fw - 30, 6, series_hdr, align="C", new_x="LMARGIN", new_y="NEXT")

    # Title
    pdf.set_xy(fx + 15, by + 45)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(font_family, "B", 24)
    pdf.multi_cell(fw - 30, 11, title.upper(), align="C")

    # Thin divider
    curr_y = pdf.get_y() + 4
    pdf.set_draw_color(201, 158, 92)
    pdf.line(fx + fw / 2 - 25, curr_y, fx + fw / 2 + 25, curr_y)

    # Subtitle
    pdf.set_xy(fx + 15, curr_y + 8)
    pdf.set_text_color(226, 232, 240)
    pdf.set_font(font_family, "I", 11)
    pdf.multi_cell(fw - 30, 6.5, subtitle, align="C")

    # Badges / Scope
    pdf.set_xy(fx + 15, by + 145)
    pdf.set_text_color(148, 163, 184)
    pdf.set_font(font_family, "", 9)
    pdf.multi_cell(
        fw - 30,
        5.5,
        badge_txt,
        align="C",
    )

    # Author
    pdf.set_xy(fx + 15, by + 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(font_family, "B", 14)
    pdf.cell(fw - 30, 8, author, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(fx + 15, by + 195)
    pdf.set_text_color(201, 158, 92)
    pdf.set_font(font_family, "", 9)
    pdf.cell(fw - 30, 5, "OPEN KNOWLEDGE FORMAT (OKF v0.2)", align="C")

    # ---------------- SPINE ----------------
    # Amazon allows spine text when spine is at least 0.25" (~6.35mm)
    sx = dims["spine_x_mm"]
    sw = dims["spine_mm"]
    if sw >= 6.35:
        # Subtle spine borders
        pdf.set_draw_color(30, 41, 59)
        pdf.line(sx, 0, sx, dims["height_mm"])
        pdf.line(sx + sw, 0, sx + sw, dims["height_mm"])

        # Rotated spine text via transform
        with pdf.rotation(270, sx + sw / 2, by + fh / 2):
            pdf.set_text_color(255, 255, 255)
            pdf.set_font(font_family, "B", 9)
            pdf.set_xy(sx + sw / 2 - 80, by + fh / 2 - 3.5)
            spine_text = f"{title.upper()}    -    {author}    -    REALIZED PRESS"
            pdf.cell(160, 7, spine_text, align="C")

    # ---------------- BACK COVER ----------------
    bx = dims["back_x_mm"]
    bw = dims["trim_w_mm"]

    # Category / Imprint top bar
    pdf.set_xy(bx + 15, by + 20)
    pdf.set_text_color(201, 158, 92)
    pdf.set_font(font_family, "B", 8.5)
    pdf.cell(bw - 30, 5, category_txt, align="L")

    # Title on back
    pdf.set_xy(bx + 15, by + 30)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(font_family, "B", 13)
    pdf.cell(bw - 30, 7, back_title_txt, align="L")

    # Blurb Paragraphs
    pdf.set_text_color(226, 232, 240)
    pdf.set_font(font_family, "", 8.5)
    curr_by = by + 40
    for para in blurb_paragraphs:
        pdf.set_xy(bx + 15, curr_by)
        pdf.multi_cell(bw - 30, 4.8, para, align="L")
        curr_by = pdf.get_y() + 3

    # Feature List
    pdf.set_xy(bx + 15, curr_by + 2)
    pdf.set_text_color(201, 158, 92)
    pdf.set_font(font_family, "B", 8.5)
    pdf.cell(bw - 30, 5, feat_hdr, align="L")

    curr_by = pdf.get_y() + 6
    pdf.set_text_color(203, 213, 225)
    pdf.set_font(font_family, "", 8)
    for feat in features:
        pdf.set_xy(bx + 18, curr_by)
        pdf.cell(bw - 36, 4.5, feat, align="L")
        curr_by += 4.5

    # Barcode locus box (50.8 mm x 30.5 mm = 2" x 1.2")
    barcode_w = 50.8
    barcode_h = 30.48
    barcode_x = bx + bw - barcode_w - 15
    barcode_y = by + fh - barcode_h - 15

    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(148, 163, 184)
    pdf.rect(barcode_x, barcode_y, barcode_w, barcode_h, style="FD")

    pdf.set_xy(barcode_x, barcode_y + 10)
    pdf.set_text_color(71, 85, 105)
    pdf.set_font(font_family, "", 7)
    pdf.cell(barcode_w, 4, "ISBN / EAN BARCODE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(barcode_x, barcode_y + 15)
    pdf.cell(barcode_w, 4, "KDP Safe Zone (2.0\" x 1.2\")", align="C")

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Amazon KDP 6\"x9\" wrap cover PDF.")
    parser.add_argument("book", default="series/parenthood-atlas", nargs="?", help="Series or book directory")
    parser.add_argument("--pages", type=int, default=None, help="Interior page count (defaults to inspecting interior PDF)")
    parser.add_argument("--paper", choices=["white", "cream"], default="white", help="Paper type (white=0.002252in, cream=0.0025in)")
    args = parser.parse_args(argv[1:] if argv else None)

    book_dir = Path(args.book).resolve()
    pub_dir = book_dir / "publishing"

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
            page_count = 145
            print(f"[kdp-cover] Interior PDF not found, defaulting to {page_count} pages")

    dims = calculate_dimensions(page_count, args.paper)
    output_pdf = (
        pub_dir / f"{base_name}-kdp-cover.pdf"
        if base_name != book_dir.name
        else pub_dir / f"{book_dir.name}-kdp-cover.pdf"
    )
    fonts = resolve_serif_fonts()

    title = "Parenthood: The Atlas"
    subtitle = "A Longitudinal Evidence Map of Developmental Science from Preconception Through Age Three"
    author = "Jose Campos"
    blurb = [
        "Parenthood: The Atlas is a longitudinal evidence atlas of developmental science from roughly one year before conception through age three. It distinguishes three non-collapsible domains: what science can observe, what interpretation suggests, and what the relational art of caregiving demands.",
        "Rather than prescriptive parenting manuals or single-study alarmism, this work presents a systematic natural-history map across fifteen curated developmental milestones. Every claim is calibrated to verified empirical certainty grades under the Open Knowledge Format.",
        "From the placental filtration of maternal cortisol to the emergence of communicative turns, from neonatal transition physiology to the fragile mechanics of toddler self-regulation, The Atlas offers parents and practitioners an unpadded, evidence-anchored foundation.",
    ]
    publishing_copy = None

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
            publishing_copy = manifest.get("publishing_copy")
            if publishing_copy and "blurb" in publishing_copy:
                blurb = publishing_copy["blurb"]
        except Exception:
            pass

    render_kdp_cover(
        title=title,
        subtitle=subtitle,
        author=author,
        blurb_paragraphs=blurb,
        dims=dims,
        output_pdf=output_pdf,
        fonts=fonts,
        publishing_copy=publishing_copy,
    )

    print(f"[kdp-cover:PASS] Wrote {output_pdf.relative_to(ROOT)} ({output_pdf.stat().st_size:,} bytes)")
    print(f"  Spine width: {dims['spine_in']:.4f}\" ({dims['spine_mm']:.2f} mm)")
    print(f"  Total cover size: {dims['width_in']:.4f}\" x {dims['height_in']:.4f}\" ({dims['width_mm']:.2f} x {dims['height_mm']:.2f} mm)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
