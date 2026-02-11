import pytest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import from api
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from api.database import engine, get_session
from api.main import app
from sqlmodel import Session, SQLModel
from contextlib import contextmanager
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    # Create tables
    SQLModel.metadata.create_all(bind=engine)
    yield engine
    # Cleanup if needed


@pytest.fixture(scope="function")
def override_get_session(test_db):
    """Override the get_session dependency for tests"""
    # Create a new session for each test
    with Session(test_db) as session:
        def get_test_session():
            return session
        
        app.dependency_overrides[get_session] = get_test_session
        yield session
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture(scope="function")
def test_client(override_get_session):
    """Create a test client with overridden dependencies"""
    with TestClient(app) as client:
        yield client