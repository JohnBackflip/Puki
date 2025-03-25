import pytest
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

@pytest.fixture
def test_client():
    from fastapi.testclient import TestClient
    from housekeeping.main import app
    return TestClient(app)

@pytest.fixture
def test_db():
    from housekeeping.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 