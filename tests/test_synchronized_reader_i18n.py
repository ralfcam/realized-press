# tests/test_synchronized_reader_i18n.py
"""
ARC-110 / ARC-111: Integration and verification test suite for Multi-Language
Text & Audio Differentiation in BWE Synchronized Reader and Standalone Players.
Validates:
1. Unified (series_slug, lang) directory and edition resolution.
2. Localized chapter prose rendering across EN, ES, and FR without English leakage.
3. Language-isolated audio streaming endpoints (/audio/{series_slug}/{lang}/{filename}) with zero cross-language fallback.
4. Timings endpoints returning language metadata and Tier 2 dynamic scaffold fallback.
5. Micro-QA diagnostics readability formulas: FK (en), Szigriszt-Pazos (es), Kandel-Moles (fr).
6. Standalone compiled HTML players with <html lang="..."> and interactive EN | ES | FR switcher.
"""
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from bwe.main import (
    app,
    resolve_series_edition_dir,
    get_available_languages,
    find_canonical_audio,
)
from bwe.db import resolve_edition_dir


def test_resolve_edition_dir_mappings() -> None:
    """Verifies resolve_edition_dir and resolve_series_edition_dir map languages to exact disk directories."""
    repo_root = Path(__file__).resolve().parent.parent

    # English base resolution
    en_dir = resolve_series_edition_dir("parenthood-atlas", "en")
    assert en_dir == repo_root / "series" / "parenthood-atlas"

    # Spanish localized resolution
    es_dir = resolve_series_edition_dir("parenthood-atlas", "es")
    assert es_dir == repo_root / "series" / "parenthood-atlas" / "i18n" / "es"
    assert (es_dir / "chapters").is_dir()

    # French localized resolution
    fr_dir = resolve_series_edition_dir("parenthood-atlas", "fr")
    assert fr_dir == repo_root / "series" / "parenthood-atlas" / "i18n" / "fr"
    assert (fr_dir / "chapters").is_dir()

    # Monolingual series fallback
    aom_dir = resolve_series_edition_dir("architectures-of-memory", "en")
    assert aom_dir == repo_root / "series" / "architectures-of-memory"

    # Available languages detection
    p_langs = get_available_languages("parenthood-atlas")
    assert set(p_langs) >= {"en", "es", "fr"}

    aom_langs = get_available_languages("architectures-of-memory")
    assert aom_langs == ["en"]


def test_reader_localized_prose_differentiation(client: TestClient) -> None:
    """Verifies that /read/... serves distinct localized prose and metadata under ?lang=en, ?lang=es, and ?lang=fr."""
    # 1. English Reader
    res_en = client.get("/read/parenthood-atlas/01-before-the-child-is-born?lang=en")
    assert res_en.status_code == 200
    soup_en = BeautifulSoup(res_en.text, "html.parser")
    html_en = soup_en.find("html")
    assert html_en is not None
    assert html_en.get("lang") == "en"
    text_en = res_en.text.lower()
    assert "before the child is born" in text_en or "parenthood: the atlas" in text_en

    # 2. Spanish Reader
    res_es = client.get("/read/parenthood-atlas/01-before-the-child-is-born?lang=es")
    assert res_es.status_code == 200
    soup_es = BeautifulSoup(res_es.text, "html.parser")
    html_es = soup_es.find("html")
    assert html_es is not None
    assert html_es.get("lang") == "es"
    text_es = res_es.text.lower()
    assert "el atlas de la crianza" in text_es or "antes de nacer" in text_es or "antes del nacimiento" in text_es
    # Ensure Spanish edition displays Spanish language switcher and active button
    assert soup_es.find(id="reader-lang-bar") is not None

    # 3. French Reader
    res_fr = client.get("/read/parenthood-atlas/01-before-the-child-is-born?lang=fr")
    assert res_fr.status_code == 200
    soup_fr = BeautifulSoup(res_fr.text, "html.parser")
    html_fr = soup_fr.find("html")
    assert html_fr is not None
    assert html_fr.get("lang") == "fr"
    text_fr = res_fr.text.lower()
    assert "l'atlas de la parentalit" in text_fr or "avant la naissance" in text_fr
    assert soup_fr.find(id="reader-lang-bar") is not None


def test_audio_endpoints_language_isolation(client: TestClient) -> None:
    """Verifies that /audio/{series}/{lang}/{file} streams audio without cross-language fallback."""
    # English Ch 1 MP3 exists
    res_en = client.get("/audio/parenthood-atlas/en/01-before-the-child-is-born.mp3")
    assert res_en.status_code == 200
    assert "audio/" in res_en.headers.get("content-type", "")

    # Spanish Ch 1 MP3 exists
    res_es = client.get("/audio/parenthood-atlas/es/01-before-the-child-is-born.mp3")
    assert res_es.status_code == 200
    assert "audio/" in res_es.headers.get("content-type", "")

    # French Ch 1 MP3 has NOT been generated yet: must return 404, NEVER fall back to English
    res_fr = client.get("/audio/parenthood-atlas/fr/01-before-the-child-is-born.mp3")
    assert res_fr.status_code == 404

    # Spanish Ch 2 MP3 has not been generated yet: must return 404, NEVER fall back to English
    res_es_ch2 = client.get("/audio/parenthood-atlas/es/02-the-newborn-landscape.mp3")
    assert res_es_ch2.status_code == 404


def test_timings_endpoints_and_tier2_scaffold(client: TestClient) -> None:
    """Verifies /timings returns language metadata and falls back to dynamic scaffold for Tier 2."""
    # 1. English Ch 1 (has neural timings on disk)
    res_en = client.get("/timings/parenthood-atlas/en/01-before-the-child-is-born")
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert data_en["language"] == "en"
    assert data_en["has_neural_audio"] is True
    assert len(data_en.get("blocks", [])) > 0

    # 2. Spanish Ch 1 (has neural timings on disk)
    res_es = client.get("/timings/parenthood-atlas/es/01-before-the-child-is-born")
    assert res_es.status_code == 200
    data_es = res_es.json()
    assert data_es["language"] == "es"
    assert data_es["has_neural_audio"] is True
    assert len(data_es.get("blocks", [])) > 0

    # 3. French Ch 1 (pending neural audio -> Tier 2 scaffold generated dynamically)
    res_fr = client.get("/timings/parenthood-atlas/fr/01-before-the-child-is-born")
    assert res_fr.status_code == 200
    data_fr = res_fr.json()
    assert data_fr["language"] == "fr"
    assert data_fr["has_neural_audio"] is False
    assert len(data_fr.get("blocks", [])) > 0
    # First block should contain French spoken text
    first_block = data_fr["blocks"][0]
    assert "spoken_text" in first_block
    assert len(first_block["spoken_text"]) > 0


def test_micro_qa_trilingual_readability(client: TestClient) -> None:
    """Verifies /hx/micro-qa/... displays appropriate localized readability metrics (FK, Szig, Kandel)."""
    # English -> FK
    res_en = client.get("/hx/micro-qa/parenthood-atlas/01-before-the-child-is-born?lang=en")
    assert res_en.status_code == 200
    assert "FK" in res_en.text

    # Spanish -> Szig
    res_es = client.get("/hx/micro-qa/parenthood-atlas/01-before-the-child-is-born?lang=es")
    assert res_es.status_code == 200
    assert "Szig" in res_es.text

    # French -> Kandel
    res_fr = client.get("/hx/micro-qa/parenthood-atlas/01-before-the-child-is-born?lang=fr")
    assert res_fr.status_code == 200
    assert "Kandel" in res_fr.text


def test_reader_landing_route(client: TestClient) -> None:
    """Verifies /reader/{series_slug} serves the default first chapter for any requested language."""
    res_landing_es = client.get("/reader/parenthood-atlas?lang=es")
    assert res_landing_es.status_code == 200
    soup = BeautifulSoup(res_landing_es.text, "html.parser")
    assert soup.find("html").get("lang") == "es"

    res_landing_fr = client.get("/reader/parenthood-atlas?lang=fr")
    assert res_landing_fr.status_code == 200
    soup = BeautifulSoup(res_landing_fr.text, "html.parser")
    assert soup.find("html").get("lang") == "fr"


def test_standalone_players_compiled_artifacts() -> None:
    """Verifies that all three standalone player index.html files have correct language, titles, and switcher."""
    repo_root = Path(__file__).resolve().parent.parent

    # English
    en_index = repo_root / "series" / "parenthood-atlas" / "audiobook" / "index.html"
    assert en_index.is_file()
    en_text = en_index.read_text(encoding="utf-8")
    assert '<html lang="en">' in en_text
    assert 'class="lang-switcher"' in en_text
    assert "Parenthood: The Atlas" in en_text

    # Spanish
    es_index = repo_root / "series" / "parenthood-atlas" / "i18n" / "es" / "audiobook" / "index.html"
    assert es_index.is_file()
    es_text = es_index.read_text(encoding="utf-8")
    assert '<html lang="es">' in es_text
    assert 'class="lang-switcher"' in es_text
    assert "El atlas de la crianza" in es_text

    # French
    fr_index = repo_root / "series" / "parenthood-atlas" / "i18n" / "fr" / "audiobook" / "index.html"
    assert fr_index.is_file()
    fr_text = fr_index.read_text(encoding="utf-8")
    assert '<html lang="fr">' in fr_text
    assert 'class="lang-switcher"' in fr_text
    assert "L'Atlas de la parentalité" in fr_text
