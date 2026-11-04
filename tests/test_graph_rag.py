# tests/test_graph_rag.py
"""Comprehensive test suite for OKF v0.3 Property Graph & Graph RAG Context Engine (ARC-84).

Verifies:
1. SQLite Schema Version 4 creation, okf_nodes, okf_edges, and indexes.
2. Migration from older schemas to Version 4.
3. build_series_knowledge_graph compiling Git-native Markdown/YAML/BibTeX into graph.
4. compile_chapter_context_pack 2-hop ego-graph traversal & token budgets (< 2,500).
5. Graph Coherence Linter rules 7a-7e in scripts/audit_manuscript.py.
6. Web endpoints /hx/graph/context-pack and /hx/graph/series-map.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from bwe.db import SCHEMA_VERSION, get_db, init_db
from bwe.graph_rag import (
    build_series_knowledge_graph,
    compile_chapter_context_pack,
    generate_series_map_svg,
)
from bwe.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_schema_version_and_graph_tables():
    """Verify SCHEMA_VERSION is 4 and property graph tables/indexes exist."""
    assert SCHEMA_VERSION == 4
    conn = get_db()
    
    # Check tables exist
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "okf_nodes" in tables
    assert "okf_edges" in tables

    # Check indexes exist
    indexes = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()}
    assert "idx_okf_nodes_series_type" in indexes
    assert "idx_okf_edges_series_type" in indexes
    assert "idx_okf_edges_source_type" in indexes
    assert "idx_okf_edges_target_type" in indexes


def test_schema_migration_in_memory():
    """Verify in-place migration to version 4 creates property graph tables on older DBs."""
    mem_conn = sqlite3.connect(":memory:")
    mem_conn.row_factory = sqlite3.Row
    # Simulate version 3 DB using SQLite PRAGMA user_version
    mem_conn.execute("PRAGMA user_version = 3;")
    
    from bwe.db import _migrate
    ran = _migrate(mem_conn)
    assert ran is True
    
    # Schema version should be updated to 4
    v = mem_conn.execute("PRAGMA user_version;").fetchone()[0]
    assert v == 4
    
    # Tables should now exist
    tables = {r[0] for r in mem_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "okf_nodes" in tables
    assert "okf_edges" in tables


def test_build_series_knowledge_graph_counts():
    """Verify build_series_knowledge_graph populates expected node and edge types with series isolation."""
    conn = get_db()
    init_db(REPO_ROOT, conn=conn)

    # Check node types for parenthood-atlas
    p_nodes = conn.execute(
        "SELECT node_type, COUNT(*) as cnt FROM okf_nodes WHERE series_slug='parenthood-atlas' GROUP BY node_type"
    ).fetchall()
    p_dict = {r["node_type"]: r["cnt"] for r in p_nodes}
    assert p_dict.get("card", 0) >= 70
    assert p_dict.get("chapter", 0) == 15
    assert p_dict.get("movement", 0) >= 60
    assert p_dict.get("source", 0) >= 100

    # Check node types for architectures-of-memory
    a_nodes = conn.execute(
        "SELECT node_type, COUNT(*) as cnt FROM okf_nodes WHERE series_slug='architectures-of-memory' GROUP BY node_type"
    ).fetchall()
    a_dict = {r["node_type"]: r["cnt"] for r in a_nodes}
    assert a_dict.get("card", 0) >= 50
    assert a_dict.get("chapter", 0) >= 80
    assert a_dict.get("character", 0) >= 20

    # Check edge types
    p_edges = conn.execute(
        "SELECT edge_type, COUNT(*) as cnt FROM okf_edges WHERE series_slug='parenthood-atlas' GROUP BY edge_type"
    ).fetchall()
    pe_dict = {r["edge_type"]: r["cnt"] for r in p_edges}
    assert pe_dict.get("CITED_IN_MOVEMENT", 0) >= 200
    assert pe_dict.get("HANDS_OFF_TO", 0) == 14
    assert pe_dict.get("BACKED_BY_SOURCE", 0) >= 100


def test_chapter_context_pack_parenthood_token_budget():
    """Verify compile_chapter_context_pack produces valid CCP within < 2,500 token budget."""
    conn = get_db()
    ccp = compile_chapter_context_pack(
        series_slug="parenthood-atlas",
        chapter_slug="05-becoming-a-mind",
        repo_root=REPO_ROOT,
        conn=conn,
    )
    
    assert ccp.chapter_num == 5
    assert "Becoming a Mind" in ccp.chapter_title
    assert ccp.incoming_handoff
    assert ccp.outgoing_handoff
    assert len(ccp.epistemic_contract) > 0

    md = ccp.to_markdown()
    assert "# Chapter Context Pack: Ch.05" in md
    assert "Epistemic Verb" in md
    assert "Adjacent Handoff Envelope" in md

    # Token budget test: strictly < 2,500 tokens (typical ~1,800)
    tokens = ccp.token_estimate()
    assert 500 < tokens < 2500, f"Token estimate {tokens} outside expected bounds [500, 2500]"

    # Dictionary serialization test
    d = ccp.to_dict()
    assert d["chapter_slug"] == "05-becoming-a-mind"
    assert isinstance(d["metaphor_ledger"], list)


def test_chapter_context_pack_multibook_aom():
    """Verify compile_chapter_context_pack correctly isolates multi-book series chapters."""
    conn = get_db()
    ccp = compile_chapter_context_pack(
        series_slug="architectures-of-memory",
        book_slug="book-02-forget-gate",
        chapter_slug="04-forget-gate-missing-piece",
        repo_root=REPO_ROOT,
        conn=conn,
    )
    
    assert ccp.chapter_num == 4
    assert ccp.book_slug == "book-02-forget-gate"
    assert "The Missing Piece" in ccp.chapter_title
    
    tokens = ccp.token_estimate()
    assert tokens < 2500


def test_generate_series_map_svg():
    """Verify generate_series_map_svg produces well-formed interactive dark-mode SVG."""
    conn = get_db()
    svg = generate_series_map_svg(conn, "parenthood-atlas")
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")
    assert "OKF v0.3" in svg
    assert "Chapters" in svg
    assert "Cards" in svg


def test_graph_coherence_linter_parenthood():
    """Verify scripts/audit_manuscript.py graph coherence audit passes on parenthood-atlas."""
    import sys
    if str(REPO_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from audit_manuscript import audit_graph_coherence

    lines, violations, is_ok = audit_graph_coherence(REPO_ROOT, REPO_ROOT / "series" / "parenthood-atlas")
    assert is_ok, f"Graph coherence failed on parenthood-atlas with violations: {violations}"
    assert len(violations) == 0


def test_graph_coherence_linter_book_01():
    """Verify scripts/audit_manuscript.py graph coherence audit passes on book-01-vanishing-signal."""
    import sys
    if str(REPO_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from audit_manuscript import audit_graph_coherence

    lines, violations, is_ok = audit_graph_coherence(
        REPO_ROOT, REPO_ROOT / "series" / "architectures-of-memory" / "book-01-vanishing-signal"
    )
    assert is_ok, f"Graph coherence failed on Book 1 with violations: {violations}"
    assert len(violations) == 0


def test_web_endpoint_context_pack(client: TestClient):
    """Verify GET /hx/graph/context-pack returns 200 with HTML partial and Copy button."""
    res = client.get("/hx/graph/context-pack?series=parenthood-atlas&chapter=05-becoming-a-mind")
    assert res.status_code == 200
    assert "OKF v0.3 CCP" in res.text
    assert "Copy CCP" in res.text
    assert "Target Chapter Ego-Graph" in res.text


def test_web_endpoint_series_map(client: TestClient):
    """Verify GET /hx/graph/series-map returns 200 with image/svg+xml."""
    res = client.get("/hx/graph/series-map?series=parenthood-atlas")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/svg+xml"
    assert "<svg" in res.text


def test_graph_rag_performance_and_warm_cache():
    """Verify ensure_series_graph warm cache and context pack compilation speed."""
    import time
    from bwe.db import ensure_series_graph

    conn = get_db()
    t0 = time.perf_counter()
    rebuilt = ensure_series_graph(conn, REPO_ROOT, "architectures-of-memory")
    t1 = time.perf_counter()
    warm_ms = (t1 - t0) * 1000
    assert not rebuilt
    assert warm_ms < 50.0  # Warm fingerprint check finishes sub-50ms

    t2 = time.perf_counter()
    pack = compile_chapter_context_pack(
        series_slug="architectures-of-memory",
        book_slug="book-01-vanishing-signal",
        chapter_slug="01-rosenblatt-perceptron",
        repo_root=REPO_ROOT,
        conn=conn,
    )
    t3 = time.perf_counter()
    pack_ms = (t3 - t2) * 1000
    assert pack_ms < 50.0
    assert pack.token_estimate() < 2500


def test_typed_semantic_edges_and_cross_book_escalation():
    """Verify typed card edges (EXTENDS, BOUNDS) and CROSS_BOOK_ESCALATES edges exist."""
    conn = get_db()
    
    # Check cross-book escalation edges
    cb_rows = conn.execute(
        "SELECT COUNT(*) FROM okf_edges WHERE series_slug='architectures-of-memory' AND edge_type='CROSS_BOOK_ESCALATES'"
    ).fetchone()[0]
    assert cb_rows >= 10, f"Expected >= 10 CROSS_BOOK_ESCALATES edges in AoM, found {cb_rows}"

    # Check typed card edges
    typed_rows = conn.execute(
        "SELECT edge_type, COUNT(*) FROM okf_edges WHERE series_slug='architectures-of-memory' GROUP BY edge_type"
    ).fetchall()
    edge_types = {r[0] for r in typed_rows}
    assert "CROSS_BOOK_ESCALATES" in edge_types
    assert "ESCALATES_TO" in edge_types
    assert "CONTRADICTS_OR_BOUNDS" in edge_types or "BOUNDS" in edge_types


def test_chapter_context_pack_3_tiers():
    """Verify 3-Tier Context Pack contains Tier 1, Tier 2, and Tier 3 data structures."""
    conn = get_db()
    pack = compile_chapter_context_pack(
        series_slug="architectures-of-memory",
        book_slug="book-01-vanishing-signal",
        chapter_slug="01-rosenblatt-perceptron",
        repo_root=REPO_ROOT,
        conn=conn,
    )

    # Tier 1
    assert len(pack.epistemic_contract) > 0
    assert len(pack.quantitative_anchors) > 0
    assert pack.escalation_ledger[0]["series_ordinal"] >= 1
    assert pack.escalation_ledger[0]["book_ordinal"] >= 1
    assert "Escalation Instruction" in pack.to_markdown()

    # Tier 2
    assert len(pack.typed_causal_edges) > 0
    assert pack.incoming_handoff is not None
    assert pack.outgoing_handoff is not None
    assert "Tier 2: 2-Hop Typed Causal Argument Map" in pack.to_markdown()

    # Tier 3
    assert len(pack.suggested_unlinked_cards) > 0
    assert "Tier 3: Latent Evidence Discovery" in pack.to_markdown()

    # Budget
    assert pack.token_estimate() < 2500


def test_graph_coherence_linter_spanish():
    """Verify scripts/audit_manuscript.py graph coherence audit passes on Spanish Edition."""
    import sys
    if str(REPO_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from audit_manuscript import audit_graph_coherence

    lines, violations, is_ok = audit_graph_coherence(
        REPO_ROOT, REPO_ROOT / "series" / "parenthood-atlas" / "i18n" / "es"
    )
    assert is_ok, f"Graph coherence failed on Spanish edition with violations: {violations}"
    assert len(violations) == 0


def test_graph_coherence_linter_all_aom_books():
    """Verify graph coherence audit passes across all 5 volumes of Architectures of Memory."""
    import sys
    if str(REPO_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from audit_manuscript import audit_graph_coherence

    for book_slug in [
        "book-01-vanishing-signal",
        "book-02-forget-gate",
        "book-03-weight-of-attention",
        "book-04-context-window",
        "book-05-architecture-of-forgetting",
    ]:
        book_dir = REPO_ROOT / "series" / "architectures-of-memory" / book_slug
        lines, violations, is_ok = audit_graph_coherence(REPO_ROOT, book_dir)
        assert is_ok, f"Graph coherence failed on {book_slug} with violations: {violations}"
        assert len(violations) == 0

