"""Pytest configuration and fixtures for tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.base import Base


@pytest.fixture
def db_session():
    """Create a fresh database session for testing."""
    # Create in-memory SQLite database for testing
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestSessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    test_engine.dispose()
