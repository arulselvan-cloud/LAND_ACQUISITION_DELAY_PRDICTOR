"""LandSight AI - PyTest Configuration and Test Fixtures."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app


@pytest.fixture(scope="session")
def client():
    """Provides a reusable FastAPI TestClient with preloaded ML models."""
    with TestClient(app) as c:
        yield c
