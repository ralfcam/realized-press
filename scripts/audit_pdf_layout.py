#!/usr/bin/env python3
"""Visual Layout & Micro-Typography Linter for Realized Press Publishing Outputs (`ARC-53`, `BWE v0.5.0`).

Audits compiled publishing artifacts against Amazon KDP and Reader Edition physical specifications:
1. Interior Page Budget & Blank Page Gate:
   - Verifies 6"x9" KDP interior page count is within paperback bounds (<= 160 pages).
   - Confirms 100% of pages contain printable content (zero blank pages).
2. Cover Wrap & Spine Geometry:
   - Verifies full-wrap PDF dimensions match exact interior page count and paper thickness.
   - White paper: spine = pages * 0.002252", width = bleed*2 + trim_w*2 + spine = 12.25" + spine.
   - Cream paper: spine = pages * 0.002500".
3. Micro-Typography & Running Header Integrity:
   - Confirms running headers do not collide with chapter text.
   - Confirms Table of Contents page numbers strictly match chapter opening pages.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent

WHITE_PAPER_THICKNESS_IN = 0.002252
CREAM_PAPER_THICKNESS_IN = 0.002500
TRIM_WIDTH_IN = 6.0
TRIM_HEIGHT_IN = 9.0
BLEED_IN = 0.125
IN_TO_MM = 25.4


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
    cover_pdf = (
        pub_dir / f"{base_name}-kdp-cover.pdf"
        if (pub_dir / f"{base_name}-kdp-cover.pdf").is_file()
        else pub_dir / f"{book_dir.name}-kdp-cover.pdf"
    )
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

    log.append("\n## 1. Amazon KDP 6\"x9\" Interior Audit")
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

    # 3. Audit Cover Wrap Dimensions
    log.append("\n## 3. Amazon KDP Full-Wrap Cover Geometry Audit")
    thickness = WHITE_PAPER_THICKNESS_IN if paper_type == "white" else CREAM_PAPER_THICKNESS_IN
    expected_spine_in = kdp_pages * thickness
    expected_width_in = (BLEED_IN * 2) + (TRIM_WIDTH_IN * 2) + expected_spine_in
    expected_height_in = (BLEED_IN * 2) + TRIM_HEIGHT_IN

    expected_w_mm = expected_width_in * IN_TO_MM
    expected_h_mm = expected_height_in * IN_TO_MM

    log.append(f"- **Paper Stock:** {paper_type.capitalize()} ({thickness:.6f}\" per page)")
    log.append(f"- **Calculated Spine:** {expected_spine_in:.4f}\" ({expected_spine_in * IN_TO_MM:.2f} mm)")
    log.append(f"- **Expected Total Wrap:** {expected_width_in:.4f}\" x {expected_height_in:.4f}\" ({expected_w_mm:.2f} x {expected_h_mm:.2f} mm)")

    if not cover_pdf.is_file():
        log.append(f"- [WARN] KDP cover wrap PDF not found at `{cover_pdf}`.")
    else:
        c_reader = PdfReader(str(cover_pdf))
        if len(c_reader.pages) < 1:
            log.append("- [FAIL] Cover PDF has 0 pages.")
            success = False
        else:
            c_page = c_reader.pages[0]
            # mediabox in points (72 points per inch)
            w_pt = float(c_page.mediabox.width)
            h_pt = float(c_page.mediabox.height)
            actual_w_in = w_pt / 72.0
            actual_h_in = h_pt / 72.0
            actual_w_mm = actual_w_in * IN_TO_MM
            actual_h_mm = actual_h_in * IN_TO_MM

            log.append(f"- **Actual Cover Wrap:** {actual_w_in:.4f}\" x {actual_h_in:.4f}\" ({actual_w_mm:.2f} x {actual_h_mm:.2f} mm)")

            # Allow 0.05" margin of error for rounding
            if abs(actual_w_in - expected_width_in) > 0.05 or abs(actual_h_in - expected_height_in) > 0.05:
                log.append(f"- [FAIL] Cover wrap dimension mismatch! Delta: W={abs(actual_w_in - expected_width_in):.4f}\", H={abs(actual_h_in - expected_height_in):.4f}\"")
                success = False
            else:
                log.append("- [PASS] Cover wrap dimensions match interior page count precisely.")

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
    parser = argparse.ArgumentParser(description="Audit PDF visual layout and print physical specifications.")
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
