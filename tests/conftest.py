# tests/conftest.py
"""
Shared pytest fixtures and test infrastructure for Realized Press BWE.
Provides session-level database initialization and reusable FastAPI TestClient fixtures.
"""
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from bwe.main import app
from bwe.db import init_db

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> None:
    """
    Session-scoped database initialization fixture.
    Ensures SQLite FTS5 manuscript virtual tables, telemetry tables,
    and keyword signal caches are properly seeded before tests run.
    """
    init_db(REPO_ROOT)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Standard FastAPI TestClient fixture with proper lifespan context management.
    Ensures startup/lifespan hooks run cleanly.
    """
    with TestClient(app) as test_client:
        yield test_client
