"""Pytest configuration and shared fixtures for all tests.

Provides:
- Isolated temporary database for each test
- API client with test database
- Pre-populated database fixtures
"""

import pytest
import sqlite3
import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch

from fastapi.testclient import TestClient

# Add parent directory to path so imports work
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from db.manager import DatabaseManager, get_connection
from db.migrations import MigrationManager, ALL_MIGRATIONS
from tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
    make_compatible_four_layers,
    AnalyteFactory,
    BioRecognitionLayerFactory,
    ImmobilizationLayerFactory,
    MemristiveLayerFactory,
)


@pytest.fixture
def tmp_db(tmp_path: Path) -> Generator[DatabaseManager, None, None]:
    """Create isolated temporary database for each test.

    Creates a fresh SQLite database in tmp_path with all tables
    initialized through migrations.

    Args:
        tmp_path: pytest temporary directory

    Yields:
        DatabaseManager instance connected to temp database
    """
    db_path = tmp_path / "test.db"
    db_url = str(db_path)

    # Patch the database connection to use our temp database
    def get_test_connection():
        conn = sqlite3.connect(db_url)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # Create manager with temp database
    original_get_connection = sys.modules['db.manager'].get_connection
    sys.modules['db.manager'].get_connection = get_test_connection

    try:
        db_manager = DatabaseManager(db_name=db_url)
        yield db_manager
    finally:
        # Cleanup
        sys.modules['db.manager'].get_connection = original_get_connection
        if db_path.exists():
            db_path.unlink()


@pytest.fixture
def api_client(tmp_db: DatabaseManager) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with isolated database.

    Patches the global database manager in main.py to use the test database.

    Args:
        tmp_db: Temporary database fixture

    Yields:
        TestClient configured with test database
    """
    # Replace the global db_manager in main.py
    import main
    original_db_manager = main.db_manager
    main.db_manager = tmp_db

    try:
        client = TestClient(app)
        yield client
    finally:
        # Restore original
        main.db_manager = original_db_manager


@pytest.fixture
def db_with_analytes(api_client: TestClient) -> TestClient:
    """Database pre-populated with 5 test analytes.

    Args:
        api_client: API test client fixture

    Returns:
        TestClient with analytes created
    """
    # Reset factory counter
    AnalyteFactory.reset_counter()

    for i in range(5):
        analyte = make_analyte()
        response = api_client.post(
            "/api/analytes",
            json=analyte,
        )
        assert response.status_code in [200, 201], f"Failed to create analyte {i}: {response.text}"

    return api_client


@pytest.fixture
def db_with_full_passport(
    api_client: TestClient,
) -> TestClient:
    """Database pre-populated with compatible sensor layers.

    Creates one analyte, one bio-recognition layer, one immobilization layer,
    and one memristive layer that are all compatible.

    Args:
        api_client: API test client fixture

    Returns:
        TestClient with full passport created
    """
    # Reset factory counters
    AnalyteFactory.reset_counter()
    BioRecognitionLayerFactory.reset_counter()
    ImmobilizationLayerFactory.reset_counter()
    MemristiveLayerFactory.reset_counter()

    analyte, bio_layer, immob_layer, mem_layer = make_compatible_four_layers()

    # Create analyte
    response = api_client.post("/api/analytes", json=analyte)
    assert response.status_code in [200, 201], f"Failed to create analyte: {response.text}"

    # Create bio-recognition layer
    response = api_client.post("/api/bio-recognition", json=bio_layer)
    assert response.status_code in [200, 201], f"Failed to create bio layer: {response.text}"

    # Create immobilization layer
    response = api_client.post("/api/immobilization", json=immob_layer)
    assert response.status_code in [200, 201], f"Failed to create immobilization layer: {response.text}"

    # Create memristive layer
    response = api_client.post("/api/memristive", json=mem_layer)
    assert response.status_code in [200, 201], f"Failed to create memristive layer: {response.text}"

    return api_client


@pytest.fixture(autouse=True)
def reset_factories():
    """Auto-reset factory counters before each test for deterministic IDs."""
    AnalyteFactory.reset_counter()
    BioRecognitionLayerFactory.reset_counter()
    ImmobilizationLayerFactory.reset_counter()
    MemristiveLayerFactory.reset_counter()
    yield
