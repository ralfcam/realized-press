from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from bwe.schema import CoverArtSpec, CoverLayoutMode, validate_series_yaml
from scripts.audit_epub import audit_epub
from scripts.audit_pdf_layout import audit_pdf_layout, extract_pdf_page_image_dimensions
from scripts.generate_cover_art import (
    NEGATIVE_TYPOGRAPHY_GUARD,
    compute_effective_dpi,
    generate_cover_artwork,
    select_best_image_part,
    synthesize_cover_prompt,
)
from scripts.render_kdp_cover import (
    calculate_dimensions,
    render_kdp_cover,
    resolve_cover_asset_path,
)
from scripts.render_publishing_pdfs import build_kdp_epub


def _make_png_bytes(width: int, height: int, color: tuple[int, int, int] = (17, 24, 39)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_cover_art_schema_validation_across_all_series() -> None:
    m_en = validate_series_yaml(ROOT / "series" / "parenthood-atlas" / "series.yaml")
    assert m_en.cover_art.layout_mode == CoverLayoutMode.FRONT_HERO_VIGNETTE
    assert m_en.cover_art.image_size == "2K"
    assert m_en.cover_art.aspect_ratio == "1:1"
    assert m_en.cover_art.prompt and "three concentric developmental rings" in m_en.cover_art.prompt

    m_es = validate_series_yaml(ROOT / "series" / "parenthood-atlas" / "i18n" / "es" / "series.yaml")
    assert m_es.cover_art.layout_mode == CoverLayoutMode.FRONT_HERO_VIGNETTE
    assert m_es.translation_of == "parenthood-atlas"

    m_aom = validate_series_yaml(ROOT / "series" / "architectures-of-memory" / "series.yaml")
    assert len(m_aom.books) == 5
    for book in m_aom.books:
        assert book.cover_art is not None
        assert book.cover_art.style_preset == "swiss-modernist-architectural-etching"
        assert book.cover_art.prompt and "Swiss modernist architectural etching" in book.cover_art.prompt


def test_prompt_synthesis_enforces_negative_typography_guard() -> None:
    for mode in [
        CoverLayoutMode.FRONT_HERO_VIGNETTE,
        CoverLayoutMode.FRONT_FULL_BLEED,
        CoverLayoutMode.FULL_WRAP_CANVAS,
    ]:
        spec = CoverArtSpec(layout_mode=mode, prompt="Test visual motif")
        synthesized = synthesize_cover_prompt(spec, title="Test Book", subtitle="Test Sub")
        assert NEGATIVE_TYPOGRAPHY_GUARD in synthesized
        if mode == CoverLayoutMode.FRONT_FULL_BLEED:
            assert "upper 32% and lower 18%" in synthesized
        elif mode == CoverLayoutMode.FULL_WRAP_CANVAS:
            assert "panoramic widescreen" in synthesized


def test_multi_part_resolution_guard_selects_largest_image_part() -> None:
    """Verify gemini-3.1-flash-image 1K preview + 2K master multi-part response selects the 2K part."""
    preview_1k = _make_png_bytes(1024, 1024, (20, 30, 40))
    master_2k = _make_png_bytes(2048, 2048, (217, 119, 6))

    parts = [
        SimpleNamespace(text="Thinking about composition..."),
        SimpleNamespace(inline_data=SimpleNamespace(data=preview_1k, mime_type="image/png")),
        SimpleNamespace(inline_data=SimpleNamespace(data=master_2k, mime_type="image/png")),
    ]
    selected_bytes, w, h, mime = select_best_image_part(parts)
    assert (w, h) == (2048, 2048)
    assert selected_bytes == master_2k
    assert mime == "image/png"


def test_generate_cover_artwork_with_mock_client_and_fallback(tmp_path: Path) -> None:
    book_dir = tmp_path / "mock-book"
    book_dir.mkdir(parents=True)
    (book_dir / "series.yaml").write_text(
        """
slug: mock-book
title: "Mock Atlas"
subtitle: "Testing Gemini Cover Pipeline"
lenses: [science, interpretation, art]
cover_art:
  layout_mode: front_hero_vignette
  aspect_ratio: "1:1"
  image_size: "2K"
  prompt: "A golden astrolabe on midnight slate"
books:
  - id: book-01-mock
    title: "Mock Atlas"
""",
        encoding="utf-8",
    )

    master_2k = _make_png_bytes(2048, 2048, (17, 24, 39))
    calls: list[str] = []

    class MockModels:
        def generate_content(self, model: str, contents: str, config: object) -> object:
            calls.append(model)
            if model == "gemini-3-pro-image":
                raise RuntimeError("429 Resource Exhausted: quota exceeded")
            return SimpleNamespace(
                candidates=[
                    SimpleNamespace(
                        content=SimpleNamespace(
                            parts=[
                                SimpleNamespace(inline_data=SimpleNamespace(data=_make_png_bytes(1024, 1024), mime_type="image/png")),
                                SimpleNamespace(inline_data=SimpleNamespace(data=master_2k, mime_type="image/png")),
                            ]
                        )
                    )
                ]
            )

    mock_client = SimpleNamespace(models=MockModels())
    out_path = generate_cover_artwork(target_dir=book_dir, client=mock_client, force=True)

    assert out_path.is_file()
    assert calls == ["gemini-3-pro-image", "gemini-3.1-flash-image"]

    meta_path = out_path.with_suffix(".meta.json")
    assert meta_path.is_file()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["model_id"] == "gemini-3.1-flash-image"
    assert meta["width_px"] == 2048
    assert meta["height_px"] == 2048
    assert meta["effective_dpi"] >= 460.0


def test_fpdf2_compositing_and_300_dpi_audit_gate(tmp_path: Path) -> None:
    book_dir = tmp_path / "test-book"
    pub_dir = book_dir / "publishing"
    assets_dir = pub_dir / "assets"
    assets_dir.mkdir(parents=True)

    # Create a valid 10-page 6x9 KDP interior PDF so audit_pdf_layout can inspect it
    from fpdf import FPDF

    interior_pdf_path = pub_dir / "test-book-kdp-6x9.pdf"
    ipdf = FPDF(unit="mm", format=(152.4, 228.6))
    for p in range(1, 11):
        ipdf.add_page()
        ipdf.set_font("Helvetica", size=11)
        ipdf.cell(0, 10, f"Chapter page {p} body text")
    ipdf.output(str(interior_pdf_path))

    # 1. High-DPI (2048x2048 -> 465.5 DPI) cover art passes audit_pdf_layout
    hi_art = assets_dir / "cover-art.png"
    hi_art.write_bytes(_make_png_bytes(2048, 2048, (25, 35, 55)))

    dims = calculate_dimensions(10, "white")
    cover_pdf_path = pub_dir / "test-book-kdp-cover.pdf"
    render_kdp_cover(
        title="Test Book",
        subtitle="A Verified Subtitle",
        author="Jose Campos",
        blurb_paragraphs=["Paragraph one.", "Paragraph two."],
        dims=dims,
        output_pdf=cover_pdf_path,
        art_path=hi_art,
    )
    assert cover_pdf_path.is_file()
    assert (assets_dir / "front-cover-ebook.png").is_file()

    ok, log = audit_pdf_layout(book_dir, paper_type="white")
    assert ok is True, "\n".join(log)
    assert any("exceeds KDP 300 DPI print threshold" in line for line in log)

    # 2. Low-DPI (512x512 -> 116.4 DPI) cover art fails audit_pdf_layout
    lo_art = assets_dir / "low-res.png"
    lo_art.write_bytes(_make_png_bytes(512, 512, (25, 35, 55)))
    render_kdp_cover(
        title="Test Book",
        subtitle="A Verified Subtitle",
        author="Jose Campos",
        blurb_paragraphs=["Paragraph one."],
        dims=dims,
        output_pdf=cover_pdf_path,
        art_path=lo_art,
    )
    ok_low, log_low = audit_pdf_layout(book_dir, paper_type="white")
    assert ok_low is False
    assert any("below KDP print minimum (300 DPI)" in line for line in log_low)


    # 3. Verify front_full_bleed (2:3 4K 2730x4096) and full_wrap_canvas (16:9 4K 5460x3072) pass 300-DPI gate
    for mode, (w_px, h_px) in [
        ("front_full_bleed", (2730, 4096)),
        ("full_wrap_canvas", (5460, 3072)),
    ]:
        mode_art = assets_dir / f"art-{mode}.png"
        mode_art.write_bytes(_make_png_bytes(w_px, h_px, (15, 23, 42)))
        (assets_dir / "cover-art.meta.json").write_text(json.dumps({"layout_mode": mode}), encoding="utf-8")
        render_kdp_cover(
            title="Test Book",
            subtitle="A Verified Subtitle",
            author="Jose Campos",
            blurb_paragraphs=["Paragraph one."],
            dims=dims,
            output_pdf=cover_pdf_path,
            art_path=mode_art,
            layout_mode_override=mode,
        )
        ok_m, log_m = audit_pdf_layout(book_dir, paper_type="white")
        assert ok_m is True, "\n".join(log_m)
        assert any("exceeds KDP 300 DPI print threshold" in line for line in log_m)


def test_i18n_inherits_parent_series_cover_art_and_epub_embeds_cover(tmp_path: Path) -> None:
    series_dir = tmp_path / "parenthood-atlas"
    es_dir = series_dir / "i18n" / "es"
    parent_assets = series_dir / "publishing" / "assets"
    parent_assets.mkdir(parents=True)
    es_dir.mkdir(parents=True)

    master_png = parent_assets / "cover-art.png"
    master_png.write_bytes(_make_png_bytes(2048, 2048, (17, 24, 39)))

    resolved = resolve_cover_asset_path(es_dir)
    assert resolved is not None and resolved.is_file()
    assert resolved == es_dir / "publishing" / "assets" / "cover-art.png"

    # Test EPUB 3 cover embedding and audit_epub verification
    ch_dir = es_dir / "chapters"
    ch_dir.mkdir(parents=True)
    ch1 = ch_dir / "01-intro.md"
    ch1.write_text("# 1. Introducción\n\nTexto del capítulo uno.\n", encoding="utf-8")

    epub_out = es_dir / "publishing" / "parenthood-atlas-kdp.epub"
    epub_out.parent.mkdir(parents=True, exist_ok=True)
    build_kdp_epub(
        book_title="El atlas de la crianza",
        author="Jose Campos",
        chapters=[ch1],
        epub_path=epub_out,
        language="es",
        cover_image_path=resolved,
    )
    ok_epub, epub_notes = audit_epub(epub_out)
    assert ok_epub is True, "\n".join(epub_notes)
    assert any("Cover image: item='cover-image'" in n for n in epub_notes)
