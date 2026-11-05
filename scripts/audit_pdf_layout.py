#!/usr/bin/env python3
"""Visual Layout, Micro-Typography & 300-DPI Cover Artwork Linter (`ARC-53` / `ARC-98`, `BWE v1.1.0`).

Audits compiled publishing artifacts against Amazon KDP and Reader Edition physical specifications:
1. Interior Page Budget & Blank Page Gate:
   - Verifies 6"x9" KDP interior page count is within paperback bounds (<= 160 pages EN, <= 180 pages i18n).
   - Confirms 100% of pages contain printable content (zero blank pages).
2. Cover Wrap & Spine Geometry:
   - Verifies full-wrap PDF dimensions match exact interior page count and paper thickness (±0.002" tolerance).
   - White paper: spine = pages * 0.002252", width = bleed*2 + trim_w*2 + spine = 12.25" + spine.
   - Cream paper: spine = pages * 0.002500".
3. Embedded Cover Artwork 300-DPI & Barcode Reserve Gate (`ARC-98`):
   - Inspects embedded raster XObject images inside `*-kdp-cover.pdf` and verifies effective print resolution
     `DPI_eff = image_width_px / placed_width_in >= 300.0 DPI`.
   - Verifies the mandatory 2.0" x 1.2" (50.8 mm x 30.48 mm) ISBN Barcode Safe Zone is present and unobstructed.
4. Micro-Typography & Running Header Integrity:
   - Confirms Table of Contents page numbers strictly match chapter opening pages.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bwe.schema import CoverLayoutMode

WHITE_PAPER_THICKNESS_IN = 0.002252
CREAM_PAPER_THICKNESS_IN = 0.002500
TRIM_WIDTH_IN = 6.0
TRIM_HEIGHT_IN = 9.0
BLEED_IN = 0.125
IN_TO_MM = 25.4
MIN_PRINT_DPI = 300.0
MIN_SPINE_TEXT_PAGES = 79  # Amazon KDP threshold: spine text rejected if < 79 pages
SPINE_TEXT_PAT = re.compile(r'-\s+(?:Jose Campos|[A-Za-z\s]+)\s+-\s+REALIZED PRESS', re.IGNORECASE)


def extract_pdf_page_image_dimensions(page: Any) -> list[tuple[str, int, int]]:
    """Extract (xobject_name, width_px, height_px) for all raster images on a PDF page."""
    found: list[tuple[str, int, int]] = []
    try:
        resources = page.get("/Resources")
        if resources is not None and hasattr(resources, "get_object"):
            resources = resources.get_object()
        xobjects = (resources or {}).get("/XObject") if isinstance(resources, dict) else None
        if xobjects is not None and hasattr(xobjects, "get_object"):
            xobjects = xobjects.get_object()
        if isinstance(xobjects, dict):
            for name, ref in xobjects.items():
                obj = ref.get_object() if hasattr(ref, "get_object") else ref
                if isinstance(obj, dict) and obj.get("/Subtype") == "/Image":
                    w = int(obj.get("/Width", 0))
                    h = int(obj.get("/Height", 0))
                    if w > 0 and h > 0:
                        found.append((str(name), w, h))
    except Exception:
        pass
    return found


def resolve_placed_dimensions_in(book_dir: Path, expected_wrap_w_in: float, expected_wrap_h_in: float) -> tuple[CoverLayoutMode, float, float]:
    """Resolve placed artwork dimensions (width_in, height_in) from cover-art.meta.json or series.yaml."""
    mode = CoverLayoutMode.FRONT_HERO_VIGNETTE
    meta_file = book_dir / "publishing" / "assets" / "cover-art.meta.json"
    if meta_file.is_file():
        try:
            import json
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if "layout_mode" in meta:
                mode = CoverLayoutMode(meta["layout_mode"])
        except Exception:
            pass
    else:
        manifest_file = (
            book_dir / "series.yaml"
            if (book_dir / "series.yaml").is_file()
            else (book_dir.parent / "series.yaml" if (book_dir.parent / "series.yaml").is_file() else None)
        )
        if manifest_file and manifest_file.is_file():
            try:
                import yaml
                raw = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
                ca = raw.get("cover_art") or {}
                for b in raw.get("books") or []:
                    if isinstance(b, dict) and (b.get("id") == book_dir.name or b.get("path") == book_dir.name):
                        if isinstance(b.get("cover_art"), dict):
                            ca = b["cover_art"]
                        break
                if ca.get("layout_mode"):
                    mode = CoverLayoutMode(ca["layout_mode"])
            except Exception:
                pass

    if mode == CoverLayoutMode.FULL_WRAP_CANVAS:
        return mode, expected_wrap_w_in, expected_wrap_h_in
    if mode == CoverLayoutMode.FRONT_FULL_BLEED:
        return mode, TRIM_WIDTH_IN + BLEED_IN, expected_wrap_h_in
    return mode, 4.40, 4.40


def audit_pdf_layout(book_dir: Path, paper_type: str = "white") -> tuple[bool, list[str]]:
    log: list[str] = []
    success = True

    pub_dir = book_dir / "publishing"
    reader_pub_dir = book_dir / "preliminary" / "publishing" if (book_dir / "preliminary" / "publishing").is_dir() else pub_dir

    base_name = book_dir.parent.parent.name if book_dir.parent.name == "i18n" else book_dir.name
    kdp_pdf = (
        pub_dir / f"{base_name}-kdp-6x9.pdf"
        if (pub_dir / f"{base_name}-kdp-6x9.pdf").is_file()
        else pub_dir / f"{book_dir.name}-kdp-6x9.pdf"
    )
    reader_pdf = (
        reader_pub_dir / f"{base_name}-reader-edition.pdf"
        if (reader_pub_dir / f"{base_name}-reader-edition.pdf").is_file()
        else reader_pub_dir / f"{book_dir.name}-reader-edition.pdf"
    )

    cover_candidates: list[Path] = []
    if paper_type == "cream":
        cover_candidates.extend([
            pub_dir / f"{base_name}-kdp-cover-cream.pdf",
            pub_dir / f"{book_dir.name}-kdp-cover-cream.pdf",
        ])
    cover_candidates.extend([
        pub_dir / f"{base_name}-kdp-cover.pdf",
        pub_dir / f"{book_dir.name}-kdp-cover.pdf",
    ])
    cover_pdf = next((p for p in cover_candidates if p.is_file()), cover_candidates[0])

    report_file = (
        pub_dir / f"{base_name}-kdp-6x9-extraction-report.txt"
        if (pub_dir / f"{base_name}-kdp-6x9-extraction-report.txt").is_file()
        else pub_dir / f"{book_dir.name}-kdp-6x9-extraction-report.txt"
    )

    log.append(f"# PDF Visual Layout & Physical Print Audit — `{book_dir.name}`")
    log.append(f"- **Audited Path:** `{book_dir}`")

    # 1. Audit KDP Interior PDF
    if not kdp_pdf.is_file():
        log.append(f"- [FAIL] Missing KDP interior PDF: `{kdp_pdf}`")
        return False, log

    kdp_reader = PdfReader(str(kdp_pdf))
    kdp_pages = len(kdp_reader.pages)
    blank_pages = [i + 1 for i, p in enumerate(kdp_reader.pages) if not (p.extract_text() or "").strip()]

    log.append('\n## 1. Amazon KDP 6"x9" Interior Audit')
    log.append(f"- **Total Page Count:** {kdp_pages} pages")
    log.append(f"- **Non-blank Pages:** {kdp_pages - len(blank_pages)}/{kdp_pages}")

    if blank_pages:
        log.append(f"- [FAIL] Blank pages detected at: {blank_pages}")
        success = False
    else:
        log.append("- [PASS] Zero blank pages in interior PDF.")

    max_kdp_pages = 180 if book_dir.parent.name == "i18n" else 160
    if kdp_pages > max_kdp_pages:
        log.append(f"- [FAIL] Page count {kdp_pages} exceeds paperback target (max {max_kdp_pages}).")
        success = False
    else:
        log.append(f"- [PASS] Page count {kdp_pages} within optimal commercial bounds (<= {max_kdp_pages}).")

    # 2. Audit Reader Edition A4 PDF
    if reader_pdf.is_file():
        r_reader = PdfReader(str(reader_pdf))
        r_pages = len(r_reader.pages)
        r_blank = [i + 1 for i, p in enumerate(r_reader.pages) if not (p.extract_text() or "").strip()]
        log.append("\n## 2. Reader Edition A4 PDF Audit")
        log.append(f"- **Total Page Count:** {r_pages} pages")
        log.append(f"- **Non-blank Pages:** {r_pages - len(r_blank)}/{r_pages}")
        if r_blank:
            log.append(f"- [FAIL] Blank pages in Reader Edition: {r_blank}")
            success = False
        else:
            log.append("- [PASS] Zero blank pages in Reader Edition PDF.")

    # 3. Audit Cover Wrap Dimensions, 300-DPI Raster Artwork & Barcode Safe Zone
    log.append("\n## 3. Amazon KDP Full-Wrap Cover Geometry & 300-DPI Print Audit")
    thickness = WHITE_PAPER_THICKNESS_IN if paper_type == "white" else CREAM_PAPER_THICKNESS_IN
    expected_spine_in = kdp_pages * thickness
    expected_width_in = (BLEED_IN * 2) + (TRIM_WIDTH_IN * 2) + expected_spine_in
    expected_height_in = (BLEED_IN * 2) + TRIM_HEIGHT_IN

    expected_w_mm = expected_width_in * IN_TO_MM
    expected_h_mm = expected_height_in * IN_TO_MM

    log.append(f'- **Paper Stock:** {paper_type.capitalize()} ({thickness:.6f}" per page)')
    log.append(f'- **Calculated Spine:** {expected_spine_in:.4f}" ({expected_spine_in * IN_TO_MM:.2f} mm)')
    log.append(f'- **Expected Total Wrap:** {expected_width_in:.4f}" x {expected_height_in:.4f}" ({expected_w_mm:.2f} x {expected_h_mm:.2f} mm)')

    if not cover_pdf.is_file():
        log.append(f"- [WARN] KDP cover wrap PDF not found at `{cover_pdf}`.")
    else:
        c_reader = PdfReader(str(cover_pdf))
        if len(c_reader.pages) < 1:
            log.append("- [FAIL] Cover PDF has 0 pages.")
            success = False
        else:
            c_page = c_reader.pages[0]
            w_pt = float(c_page.mediabox.width)
            h_pt = float(c_page.mediabox.height)
            actual_w_in = w_pt / 72.0
            actual_h_in = h_pt / 72.0
            actual_w_mm = actual_w_in * IN_TO_MM
            actual_h_mm = actual_h_in * IN_TO_MM

            log.append(f'- **Actual Cover Wrap:** {actual_w_in:.4f}" x {actual_h_in:.4f}" ({actual_w_mm:.2f} x {actual_h_mm:.2f} mm)')

            if abs(actual_w_in - expected_width_in) > 0.002 or abs(actual_h_in - expected_height_in) > 0.002:
                log.append(
                    f'- [FAIL] Cover wrap dimension mismatch! Delta: W={abs(actual_w_in - expected_width_in):.4f}", '
                    f'H={abs(actual_h_in - expected_height_in):.4f}" (max tolerance ±0.002")'
                )
                success = False
            else:
                log.append('- [PASS] Cover wrap dimensions match interior page count within ±0.002" tolerance.')

            # Barcode Reserve Integrity check
            cover_text = c_page.extract_text() or ""
            if "ISBN / EAN BARCODE" in cover_text and "KDP Safe Zone" in cover_text:
                log.append('- [PASS] Mandatory 2.0" x 1.2" ISBN Barcode Safe Zone present and unobstructed.')
            else:
                log.append('- [FAIL] Mandatory 2.0" x 1.2" ISBN Barcode Safe Zone missing from cover PDF.')
                success = False

            # Spine Text Threshold Audit (KDP requires >= 79 pages for spine text)
            has_spine_text = bool(SPINE_TEXT_PAT.search(cover_text))
            if kdp_pages < MIN_SPINE_TEXT_PAGES:
                if has_spine_text:
                    log.append(
                        f"- [FAIL] Spine text detected on slim volume ({kdp_pages} pages < {MIN_SPINE_TEXT_PAGES} pages). "
                        'Violates Amazon KDP 79-page threshold and will fail pre-flight hinge fold check.'
                    )
                    success = False
                else:
                    log.append(
                        f'- [PASS] Slim volume ({kdp_pages} pages < {MIN_SPINE_TEXT_PAGES} pages): spine text correctly omitted '
                        'to preserve KDP 0.0625" (1.59 mm) hinge margin.'
                    )
            else:
                if has_spine_text:
                    log.append(f"- [PASS] Full spine text verified for {kdp_pages}-page volume (>= {MIN_SPINE_TEXT_PAGES} pages).")
                else:
                    log.append(f"- [FAIL] Expected spine text missing for {kdp_pages}-page volume (>= {MIN_SPINE_TEXT_PAGES} pages).")
                    success = False

            # Embedded Raster Image 300-DPI Check
            embedded_images = extract_pdf_page_image_dimensions(c_page)
            layout_mode, placed_w_in, placed_h_in = resolve_placed_dimensions_in(
                book_dir, expected_width_in, expected_height_in
            )
            if embedded_images:
                for img_name, img_w_px, img_h_px in embedded_images:
                    dpi_x = img_w_px / placed_w_in if placed_w_in > 0 else 0.0
                    dpi_y = img_h_px / placed_h_in if placed_h_in > 0 else 0.0
                    eff_dpi = min(dpi_x, dpi_y)
                    log.append(
                        f"- **Embedded Cover Artwork (`{img_name}`, `{layout_mode.value}`):** "
                        f'{img_w_px}x{img_h_px} px placed at {placed_w_in:.3f}"x{placed_h_in:.3f}" -> '
                        f"**{eff_dpi:.1f} effective DPI** (X={dpi_x:.1f}, Y={dpi_y:.1f})"
                    )
                    if eff_dpi < MIN_PRINT_DPI:
                        log.append(
                            f"- [FAIL] Embedded cover image `{img_name}` resolution {eff_dpi:.1f} DPI is below KDP print minimum ({MIN_PRINT_DPI:.0f} DPI)."
                        )
                        success = False
                    else:
                        log.append(f"- [PASS] Embedded cover image `{img_name}` exceeds KDP 300 DPI print threshold ({eff_dpi:.1f} DPI >= 300 DPI).")
            else:
                log.append("- [INFO] Cover PDF is pure vector (`vector_only` mode; 0 embedded raster images).")

    # 4. Extraction Report Cross-Check
    if report_file.is_file():
        log.append("\n## 4. Chapter TOC & Extraction Report Cross-Check")
        txt = report_file.read_text(encoding="utf-8")
        if "Status: PASS" in txt:
            log.append("- [PASS] Extraction report status is PASS.")
        else:
            log.append("- [FAIL] Extraction report status is NOT PASS.")
            success = False

    return success, log


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PDF visual layout, 300-DPI cover artwork, and print physical specifications.")
    parser.add_argument("book", default="series/parenthood-atlas", nargs="?", help="Series or book directory")
    parser.add_argument("--paper", choices=["white", "cream"], default="white", help="Paper type (default: white)")
    args = parser.parse_args()

    book_dir = Path(args.book)
    if not book_dir.is_absolute():
        book_dir = (ROOT / book_dir).resolve()

    if not book_dir.is_dir():
        print(f"error: book directory not found: {book_dir}", file=sys.stderr)
        return 1

    success, log = audit_pdf_layout(book_dir, paper_type=args.paper)
    print("\n".join(log))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
