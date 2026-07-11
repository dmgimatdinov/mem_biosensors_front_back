"""pytest configuration and fixtures for testing FastAPI backend."""

import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from db.manager import DatabaseManager


@pytest.fixture(scope="function")
def api_client(tmp_path):
    """
    FastAPI TestClient with temporary isolated database.
    
    Each test gets a clean, isolated database to avoid test interference.
    Uses tmp_path fixture from pytest for automatic cleanup.
    """
    # Set up temporary database for this test
    temp_db_path = str(tmp_path / "test_biosensor.db")
    os.environ["DATABASE_URL"] = temp_db_path
    
    # Create client with the app
    client = TestClient(app)
    
    yield client
    
    # Cleanup happens automatically when tmp_path is destroyed


@pytest.fixture(params=["analytes", "bio-recognition", "immobilization", "memristive"])
def entity_endpoint(request):
    """Parametrized fixture for all entity endpoints."""
    return f"/api/{request.param}"


@pytest.fixture(params=["analyte", "bio_recognition", "immobilization", "memristive"])
def entity_type(request):
    """Parametrized fixture for entity type names (used in factories)."""
    return request.param


@pytest.fixture
def entity_factory(entity_type):
    """Returns the appropriate factory function for the given entity type."""
    from tests.factories import (
        make_analyte,
        make_bio_recognition_layer,
        make_immobilization_layer,
        make_memristive_layer
    )
    
    factories = {
        "analyte": make_analyte,
        "bio_recognition": make_bio_recognition_layer,
        "immobilization": make_immobilization_layer,
        "memristive": make_memristive_layer
    }
    
    return factories[entity_type]


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
