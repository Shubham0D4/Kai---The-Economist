"""
Pytest configuration and fixtures.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gateway.database import Base, get_db
from gateway.app import app
from gateway import models

from sqlalchemy.pool import StaticPool

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def mock_llm_response():
    """Mock Google Generative AI response."""
    mock_response = MagicMock()
    mock_response.text = "Mocked LLM analysis response."
    
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model
        yield mock_model

@pytest.fixture(scope="module")
def mock_sec_filings():
    """Mock SEC filing data."""
    # Patching where it's used in CharlieAgent
    with patch("agents.charlie_fundamental.agent.fetch_filing_data") as mock_fetch:
        mock_fetch.return_value = {
            "success": True,
            "filings": [{
                "form": "10-K",
                "filing_date": "2023-12-31",
                "document_url": "http://example.com/10k"
            }],
            "company_name": "Test Corp"
        }
        yield mock_fetch

@pytest.fixture(scope="module")
def mock_news_stream():
    """Mock News Stream data."""
    with patch("mcp_server.tools.news_stream.get_news_stream") as mock_stream:
        mock_stream.return_value = {
            "success": True,
            "articles": [{
                "title": "Test News",
                "url": "http://example.com/news",
                "published_at": "2024-01-01",
                "source": "Test Source"
            }],
            "count": 1
        }
        yield mock_stream
