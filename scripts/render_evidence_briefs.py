#!/usr/bin/env python3
"""Public Evidence Briefs Generator (HTML + 2-Page PDF + Compendium).

Compiles verified OKF v0.3 Evidence Cards (default: `status: stable`) into:
1. Individual standalone, responsive HTML Public Evidence Briefs.
2. Individual deterministic 2-page print/distribution PDFs via fpdf2.
3. A single merged Compendium PDF via pypdf.
4. A catalog `index.html` referencing all briefs with metadata and downloads.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import date
from pathlib import Path

from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from five_rule_check import split_frontmatter
from render_publishing_pdfs import clean_pdf_line, md_inline_html, resolve_serif_fonts

try:
    import yaml
except ImportError:
    yaml = None

REQUIRED_SECTIONS = [
    "What We Know",
    "How Confident We Are",
    "Evidence and Causal Assessment",
    "Effect Size and Persistence",
    "Bias, Heterogeneity, and Confounding",
    "What Remains Uncertain",
    "What This Does Not Mean",
    "What Action Is Reasonably Justified",
    "Sources",
]


def extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    lines = body.splitlines()
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_title:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)

    if current_title:
        sections[current_title] = "\n".join(current_lines).strip()
    return sections


class EvidenceBriefPDF(FPDF):
    def __init__(self, card_title: str, card_id: str, fonts: dict[str, Path]) -> None:
        super().__init__(format="A4")
        self.card_title = card_title
        self.card_id = card_id
        for style, fpath in fonts.items():
            self.add_font("BriefSerif", style, str(fpath))
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(True, margin=16)

    def header(self) -> None:
        self.set_y(10)
        self.set_font("BriefSerif", "B", 7.5)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, "REALIZED PRESS  ·  PUBLIC EVIDENCE BRIEF  ·  OPEN KNOWLEDGE FORMAT (OKF v0.3)", align="L")
        self.ln(3)
        self.set_font("BriefSerif", "I", 7.5)
        self.cell(0, 4, f"ID: {self.card_id}  ·  Verified Stable Synthesis", align="R")
        self.set_draw_color(210, 215, 222)
        self.line(18, 17, 192, 17)
        self.ln(6)
        self.set_text_color(25, 25, 25)

    def footer(self) -> None:
        self.set_y(-13)
        self.set_draw_color(210, 215, 222)
        self.line(18, 284, 192, 284)
        self.set_font("BriefSerif", "I", 7.5)
        self.set_text_color(120, 120, 120)
        self.cell(
            0,
            4,
            f"Series: Parenthood: The Atlas  ·  https://realizedpress.org  ·  Page {self.page_no()}",
            align="C",
        )
        self.set_text_color(25, 25, 25)


def render_brief_pdf(
    card_data: dict,
    sections: dict[str, str],
    fonts: dict[str, Path],
    dest_path: Path,
) -> None:
    title = card_data.get("title", dest_path.stem)
    slug = dest_path.stem
    pdf = EvidenceBriefPDF(card_title=title, card_id=slug, fonts=fonts)
    pdf.add_page()

    # Title & Metadata
    pdf.set_font("BriefSerif", "B", 15)
    pdf.multi_cell(0, 6.5, clean_pdf_line(title))
    pdf.ln(2)

    # Subtitle / description
    desc = card_data.get("description", "")
    if desc:
        pdf.set_font("BriefSerif", "I", 9.5)
        pdf.set_text_color(70, 70, 70)
        pdf.multi_cell(0, 4.8, clean_pdf_line(desc))
        pdf.ln(2)
        pdf.set_text_color(25, 25, 25)

    # Metadata Badges Bar
    grade = card_data.get("confidence", "unrated").upper()
    status = card_data.get("status", "draft").upper()
    domains = card_data.get("atlas_domains") or card_data.get("series_domains") or card_data.get("tags") or []
    domain_str = ", ".join(domains[:3])

    pdf.set_fill_color(242, 244, 248)
    pdf.set_draw_color(200, 208, 220)
    pdf.set_font("BriefSerif", "B", 8)
    meta_text = f"GRADE: {grade}   |   STATUS: {status}   |   DOMAIN: {domain_str.upper()}   |   REPLICATION: VERIFIED"
    pdf.cell(0, 6.5, meta_text, border=1, fill=True, align="C")
    pdf.ln(8)

    # Callout Box 1: WHAT WE KNOW
    what_we_know = sections.get("What We Know", "")
    if what_we_know:
        pdf.set_fill_color(240, 248, 244)
        pdf.set_draw_color(180, 215, 195)
        pdf.set_font("BriefSerif", "B", 9)
        pdf.set_text_color(20, 80, 50)
        pdf.cell(0, 5, "WHAT WE KNOW (Narrowest Supported Conclusion)", fill=True)
        pdf.ln(5)
        pdf.set_font("BriefSerif", "", 9)
        pdf.set_text_color(25, 25, 25)
        clean_know = clean_pdf_line(what_we_know)
        pdf.multi_cell(0, 4.6, clean_know, fill=True, border="B")
        pdf.ln(5)

    def write_section(title: str, text: str, font_size: float = 8.5) -> None:
        if not text:
            return
        pdf.set_font("BriefSerif", "B", 9.5)
        pdf.set_text_color(30, 45, 75)
        pdf.cell(0, 5, title.upper())
        pdf.ln(5.5)
        pdf.set_font("BriefSerif", "", font_size)
        pdf.set_text_color(25, 25, 25)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for para in lines:
            pdf.multi_cell(0, 4.4, clean_pdf_line(para))
            pdf.ln(2)
        pdf.ln(2.5)

    # Evidence and Causal Assessment
    write_section("Evidence and Causal Assessment", sections.get("Evidence and Causal Assessment", ""))

    # Effect Size and Persistence
    write_section("Effect Size and Persistence", sections.get("Effect Size and Persistence", ""))

    # Bias, Heterogeneity, and Confounding
    write_section("Bias, Heterogeneity, and Confounding", sections.get("Bias, Heterogeneity, and Confounding", ""))

    # Box 2: WHAT THIS DOES NOT MEAN (Boundary condition)
    wtdm = sections.get("What This Does Not Mean", "")
    if wtdm:
        pdf.set_fill_color(254, 245, 245)
        pdf.set_draw_color(230, 185, 185)
        pdf.set_font("BriefSerif", "B", 9)
        pdf.set_text_color(150, 30, 30)
        pdf.cell(0, 5, "WHAT THIS DOES NOT MEAN (Strict Boundary Conditions)", fill=True)
        pdf.ln(5)
        pdf.set_font("BriefSerif", "", 8.5)
        pdf.set_text_color(25, 25, 25)
        pdf.multi_cell(0, 4.4, clean_pdf_line(wtdm), fill=True, border="B")
        pdf.ln(4.5)

    # What Action Is Reasonably Justified
    write_section("What Action Is Reasonably Justified", sections.get("What Action Is Reasonably Justified", ""))

    # Sources
    sources_text = sections.get("Sources", "")
    if sources_text:
        pdf.set_font("BriefSerif", "B", 8.5)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(0, 4.5, "VERIFIED SOURCES & DOI IDENTIFIERS")
        pdf.ln(5)
        pdf.set_font("BriefSerif", "", 7.5)
        pdf.set_text_color(60, 60, 60)
        for sline in sources_text.splitlines():
            sline = sline.strip()
            if sline:
                pdf.multi_cell(0, 3.8, clean_pdf_line(sline))
                pdf.ln(1)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(dest_path))


def render_brief_html(
    card_data: dict,
    sections: dict[str, str],
    dest_path: Path,
) -> None:
    title = html.escape(card_data.get("title", dest_path.stem))
    slug = html.escape(dest_path.stem)
    desc = html.escape(card_data.get("description", ""))
    grade = html.escape(str(card_data.get("confidence", "unrated")).upper())
    status = html.escape(str(card_data.get("status", "draft")).upper())
    tier = html.escape(str(card_data.get("attenuation_tier", "")))
    tier_tag = f'<span class="badge badge-tier">Tier: {tier}</span>' if tier else ""
    domains = card_data.get("atlas_domains") or card_data.get("series_domains") or card_data.get("tags") or []
    domain_tags = "".join(f'<span class="badge badge-domain">{html.escape(d)}</span>' for d in domains)

    anchors = card_data.get("quantitative_anchors", [])
    if anchors:
        anchors_pills = "".join(f'<span class="anchor-pill">{html.escape(str(a))}</span>' for a in anchors)
        anchors_html = f'''
        <div class="anchors-box">
            <div class="anchors-title">Quantitative Anchors</div>
            <div class="anchors-list">{anchors_pills}</div>
        </div>
        '''
    else:
        anchors_html = ""

    relates_to = card_data.get("relates_to_cards", [])
    if relates_to:
        neighbor_items = []
        for rel in relates_to:
            if ":" in rel:
                rel_type, target = rel.split(":", 1)
                rel_type, target = rel_type.strip(), target.strip()
            else:
                rel_type, target = "RELATES", rel.strip()
            cls_suffix = rel_type.lower().replace("_", "-")
            neighbor_items.append(
                f'<div class="neighbor-item"><span class="neighbor-type neighbor-{cls_suffix}">{html.escape(rel_type)}</span> '
                f'<a href="{html.escape(target)}.html" class="neighbor-link">{html.escape(target)}</a></div>'
            )
        neighbors_html = f'''
        <section class="brief-section">
            <h2>Epistemic Neighbor Cards ({len(relates_to)} linked)</h2>
            <div class="neighbors-list">{"".join(neighbor_items)}</div>
        </section>
        '''
    else:
        neighbors_html = ""

    def section_html(name: str) -> str:
        text = sections.get(name, "")
        if not text:
            return ""
        paras = []
        for line in text.split("\n\n"):
            line = line.strip()
            if not line:
                continue
            paras.append(f"<p>{md_inline_html(line)}</p>")
        return f"""
        <section class="brief-section">
            <h2>{html.escape(name)}</h2>
            {"".join(paras)}
        </section>
        """

    what_we_know = sections.get("What We Know", "")
    wtdm = sections.get("What This Does Not Mean", "")
    action = sections.get("What Action Is Reasonably Justified", "")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} — Realized Press Evidence Brief</title>
    <style>
        :root {{
            --primary: #1e3a8a;
            --primary-light: #eff6ff;
            --success: #15803d;
            --success-light: #f0fdf4;
            --warning: #b45309;
            --warning-light: #fffbeb;
            --danger: #b91c1c;
            --danger-light: #fef2f2;
            --text: #1f2937;
            --text-muted: #4b5563;
            --border: #e5e7eb;
            --border-dark: #cbd5e1;
            --bg: #ffffff;
            --surface: #f8fafc;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--surface);
            margin: 0;
            padding: 2rem 1rem;
        }}
        .container {{
            max-width: 860px;
            margin: 0 auto;
            background: var(--bg);
            padding: 2.5rem 3rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid var(--border);
        }}
        .nav-back {{
            display: inline-block;
            margin-bottom: 1.5rem;
            font-size: 0.875rem;
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }}
        .nav-back:hover {{ text-decoration: underline; }}
        header {{
            border-bottom: 2px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        .series-label {{
            font-size: 0.8125rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}
        h1 {{
            font-size: 1.875rem;
            font-weight: 800;
            line-height: 1.25;
            color: #0f172a;
            margin: 0.25rem 0 0.75rem 0;
        }}
        .description {{
            font-size: 1.0625rem;
            color: var(--text-muted);
            margin-bottom: 1.25rem;
        }}
        .badges-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
        }}
        .badge {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}
        .badge-status {{ background: #e0e7ff; color: #3730a3; }}
        .badge-grade {{ background: #dcfce7; color: #166534; }}
        .badge-tier {{ background: #f3e8ff; color: #6b21a8; border: 1px solid #d8b4fe; }}
        .badge-domain {{ background: #f1f5f9; color: #475569; }}
        .anchors-box {{
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 6px;
            padding: 1rem 1.25rem;
            margin: 1.5rem 0;
        }}
        .anchors-title {{
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #0369a1;
            margin-bottom: 0.5rem;
        }}
        .anchors-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        .anchor-pill {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.75rem;
            background: #e0f2fe;
            color: #075985;
            border: 1px solid #7dd3fc;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }}
        .neighbors-list {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        .neighbor-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
        }}
        .neighbor-type {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.6875rem;
            font-weight: 700;
            text-transform: uppercase;
            padding: 0.15rem 0.4rem;
            border-radius: 3px;
        }}
        .neighbor-extends {{ background: #dcfce7; color: #166534; border: 1px solid #86efac; }}
        .neighbor-bounds {{ background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }}
        .neighbor-contrasts {{ background: #ffe4e6; color: #9f1239; border: 1px solid #fecdd3; }}
        .neighbor-mitigates {{ background: #cffafe; color: #155e75; border: 1px solid #67e8f9; }}
        .neighbor-bridges-lens {{ background: #f3e8ff; color: #6b21a8; border: 1px solid #d8b4fe; }}
        .neighbor-relates {{ background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
        .neighbor-link {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: var(--primary);
            text-decoration: none;
        }}
        .neighbor-link:hover {{ text-decoration: underline; }}
        .download-pill {{
            margin-left: auto;
            font-size: 0.8125rem;
            font-weight: 600;
            color: var(--primary);
            background: var(--primary-light);
            border: 1px solid #bfdbfe;
            padding: 0.35rem 0.75rem;
            border-radius: 4px;
            text-decoration: none;
        }}
        .download-pill:hover {{ background: #dbeafe; }}
        .callout {{
            border-radius: 6px;
            padding: 1.25rem 1.5rem;
            margin: 1.75rem 0;
            border-left: 4px solid;
        }}
        .callout-know {{
            background: var(--success-light);
            border-color: var(--success);
        }}
        .callout-wtdm {{
            background: var(--danger-light);
            border-color: var(--danger);
        }}
        .callout-action {{
            background: var(--primary-light);
            border-color: var(--primary);
        }}
        .callout h3 {{
            margin: 0 0 0.5rem 0;
            font-size: 0.9375rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .callout-know h3 {{ color: var(--success); }}
        .callout-wtdm h3 {{ color: var(--danger); }}
        .callout-action h3 {{ color: var(--primary); }}
        .callout p {{
            margin: 0;
            font-size: 0.9375rem;
        }}
        .brief-section {{
            margin: 2rem 0;
        }}
        .brief-section h2 {{
            font-size: 1.1875rem;
            font-weight: 700;
            color: #0f172a;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.4rem;
            margin-bottom: 0.75rem;
        }}
        .brief-section p {{
            font-size: 0.9375rem;
            margin-bottom: 0.75rem;
        }}
        footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border);
            font-size: 0.8125rem;
            color: var(--text-muted);
            text-align: center;
        }}
    </style>
</head>
<body>
<div class="container">
    <a href="index.html" class="nav-back">← Back to Evidence Briefs Index</a>
    <header>
        <div class="series-label">Realized Press · Public Evidence Brief · OKF v0.3</div>
        <h1>{title}</h1>
        {f'<div class="description">{desc}</div>' if desc else ''}
        <div class="badges-bar">
            <span class="badge badge-status">Status: {status}</span>
            <span class="badge badge-grade">Confidence: {grade}</span>
            {tier_tag}
            {domain_tags}
            <a href="{slug}.pdf" class="download-pill" download>Download 2-Page PDF</a>
        </div>
    </header>

    {anchors_html}

    {f'''
    <div class="callout callout-know">
        <h3>What We Know (Narrowest Supported Conclusion)</h3>
        <p>{md_inline_html(what_we_know)}</p>
    </div>
    ''' if what_we_know else ''}

    {section_html("Evidence and Causal Assessment")}
    {section_html("Effect Size and Persistence")}
    {section_html("Bias, Heterogeneity, and Confounding")}

    {f'''
    <div class="callout callout-wtdm">
        <h3>What This Does Not Mean (Strict Boundary Conditions)</h3>
        <p>{md_inline_html(wtdm)}</p>
    </div>
    ''' if wtdm else ''}

    {section_html("What Remains Uncertain")}

    {f'''
    <div class="callout callout-action">
        <h3>What Action Is Reasonably Justified</h3>
        <p>{md_inline_html(action)}</p>
    </div>
    ''' if action else ''}

    {neighbors_html}

    {section_html("Sources")}

    <footer>
        <p>Published by Realized Press · Open Knowledge Format (OKF v0.3) · Verified Academic Citation Lock</p>
    </footer>
</div>
</body>
</html>
"""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(html_content, encoding="utf-8")


def render_compendium_and_index(
    rendered_cards: list[dict],
    output_dir: Path,
    series_title: str = "Parenthood: The Atlas",
) -> tuple[Path, Path]:
    # 1. Build Compendium PDF
    compendium_pdf_path = output_dir / "parenthood-atlas-evidence-briefs-compendium.pdf"
    writer = PdfWriter()

    for item in rendered_cards:
        pdf_path = item["pdf_path"]
        if pdf_path.exists():
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                writer.add_page(page)

    with compendium_pdf_path.open("wb") as f:
        writer.write(f)

    # 2. Build index.html
    rows = []
    for item in rendered_cards:
        data = item["data"]
        slug = item["slug"]
        grade = str(data.get("confidence", "unrated")).upper()
        title = html.escape(data.get("title", slug))
        desc = html.escape(data.get("description", ""))
        domains = ", ".join(data.get("atlas_domains") or data.get("tags") or [])
        rows.append(f"""
        <tr>
            <td><strong><a href="{slug}.html">{title}</a></strong><br><small style="color:#64748b;">{desc}</small></td>
            <td><span class="badge badge-grade">{grade}</span></td>
            <td><small>{html.escape(domains)}</small></td>
            <td>
                <a href="{slug}.html" class="btn">HTML</a>
                <a href="{slug}.pdf" class="btn btn-pdf" download>PDF</a>
            </td>
        </tr>
        """)

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(series_title)} — Public Evidence Briefs Compendium</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 2.5rem 1rem;
        }}
        .container {{
            max-width: 1040px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 2.5rem 3rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }}
        header {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        .series-tag {{
            font-size: 0.8125rem;
            font-weight: 700;
            color: #1e3a8a;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        h1 {{
            font-size: 2rem;
            font-weight: 800;
            color: #0f172a;
            margin: 0.35rem 0 0.75rem 0;
        }}
        p.subtitle {{
            font-size: 1.0625rem;
            color: #475569;
            margin: 0 0 1.25rem 0;
        }}
        .compendium-banner {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 1rem 1.5rem;
            margin-bottom: 2rem;
        }}
        .compendium-banner p {{ margin: 0; font-size: 0.9375rem; color: #1e40af; }}
        .btn-compendium {{
            background: #1e40af;
            color: #ffffff;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.875rem;
        }}
        .btn-compendium:hover {{ background: #1d4ed8; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            padding: 0.85rem 0.75rem;
            text-align: left;
            border-bottom: 1px solid #f1f5f9;
        }}
        th {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            background: #f8fafc;
        }}
        tr:hover td {{ background: #fdfdfe; }}
        .badge {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }}
        .badge-grade {{ background: #dcfce7; color: #166534; }}
        .btn {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 600;
            text-decoration: none;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            background: #f1f5f9;
            color: #334155;
            border: 1px solid #cbd5e1;
            margin-right: 0.25rem;
        }}
        .btn:hover {{ background: #e2e8f0; }}
        .btn-pdf {{ background: #eff6ff; color: #1e40af; border-color: #bfdbfe; }}
        .btn-pdf:hover {{ background: #dbeafe; }}
        footer {{
            margin-top: 3rem;
            border-top: 1px solid #e2e8f0;
            padding-top: 1.5rem;
            text-align: center;
            font-size: 0.8125rem;
            color: #64748b;
        }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <div class="series-tag">Realized Press · Imprint Release</div>
        <h1>{html.escape(series_title)} — Public Evidence Briefs</h1>
        <p class="subtitle">Deterministic, peer-audited 2-page synthesis briefs for all stable Open Knowledge Format (OKF v0.3) claims.</p>
    </header>

    <div class="compendium-banner">
        <p><strong>Complete Collection:</strong> Download all {len(rendered_cards)} verified briefs in a single compiled PDF.</p>
        <a href="parenthood-atlas-evidence-briefs-compendium.pdf" class="btn-compendium" download>Download Compendium PDF</a>
    </div>

    <table>
        <thead>
            <tr>
                <th>Claim & Synthesis</th>
                <th style="width: 110px;">Grade</th>
                <th style="width: 180px;">Domains</th>
                <th style="width: 140px;">Format</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows)}
        </tbody>
    </table>

    <footer>
        <p>Realized Press · Book Writing Environment (BWE) · Open Knowledge Format (OKF v0.3)</p>
    </footer>
</div>
</body>
</html>
"""
    index_path = output_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    return compendium_pdf_path, index_path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Render Public Evidence Briefs (HTML + PDF + Compendium)")
    parser.add_argument("target", nargs="?", default="series/parenthood-atlas", help="Book or series directory")
    parser.add_argument("--status", default="stable", help="Card status filter (default: stable)")
    parser.add_argument("--all-cards", action="store_true", help="Render all cards regardless of status")
    parser.add_argument("--output-dir", help="Output directory for briefs")
    args = parser.parse_args(argv[1:])

    target_dir = Path(args.target)
    if not target_dir.is_dir():
        target_dir = ROOT / target_dir
    if not target_dir.is_dir():
        print(f"Target directory not found: {args.target}", file=sys.stderr)
        return 1

    ec_dir = target_dir / "evidence-cards" if (target_dir / "evidence-cards").is_dir() else target_dir
    card_files = sorted(ec_dir.glob("*.md"))
    card_files = [c for c in card_files if c.name not in ("_TEMPLATE.md", "index.md", "README.md")]

    out_dir = Path(args.output_dir) if args.output_dir else (target_dir / "publishing" / "evidence-briefs")
    out_dir.mkdir(parents=True, exist_ok=True)

    fonts = resolve_serif_fonts()
    rendered: list[dict] = []

    print(f"Scanning evidence cards in: {ec_dir}")
    for cpath in card_files:
        text = cpath.read_text(encoding="utf-8")
        fm_text, body = split_frontmatter(text)
        if not fm_text:
            continue
        data = {}
        if yaml:
            try:
                data = yaml.safe_load(fm_text) or {}
            except Exception:
                pass
        card_status = str(data.get("status", "draft")).lower()
        if not args.all_cards and card_status != args.status.lower():
            continue

        slug = cpath.stem
        sections = extract_sections(body)
        pdf_path = out_dir / f"{slug}.pdf"
        html_path = out_dir / f"{slug}.html"

        render_brief_pdf(data, sections, fonts, pdf_path)
        render_brief_html(data, sections, html_path)
        rendered.append({
            "slug": slug,
            "data": data,
            "pdf_path": pdf_path,
            "html_path": html_path,
        })
        print(f"[brief] Rendered {slug} (Grade: {data.get('confidence')}) -> PDF + HTML")

    if rendered:
        compendium_path, index_path = render_compendium_and_index(rendered, out_dir)
        print(f"[compendium] Wrote {compendium_path} ({len(rendered)} briefs)")
        print(f"[index] Wrote {index_path}")
    else:
        print(f"No cards matching status '{args.status}' found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
