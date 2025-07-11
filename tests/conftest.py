import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import pytest
import requests_mock

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure pytest to add custom markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (deselect with '-m not integration')",
    )
    config.addinivalue_line(
        "markers",
        "unit: mark test as unit test (deselect with '-m not unit')",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (deselect with '-m not slow')",
    )

# Add command line options for API keys
def pytest_addoption(parser):
    parser.addoption(
        "--run-integration", 
        action="store_true", 
        default=False, 
        help="run integration tests with real API calls"
    )
    parser.addoption(
        "--run-slow", 
        action="store_true", 
        default=False, 
        help="run slow tests (including integration tests)"
    )

# Skip integration tests by default unless --run-integration is used
def pytest_collection_modifyitems(config, items):
    # Handle integration tests
    if config.getoption("--run-integration") or config.getoption("--run-slow"):
        return
    
    skip_integration = pytest.mark.skip(reason="need --run-integration or --run-slow option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
    
    # Handle slow tests
    if config.getoption("--run-slow"):
        return
    
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

# HTTP request mocking fixture
@pytest.fixture
def mock_requests():
    """Fixture for mocking HTTP requests."""
    with requests_mock.Mocker() as m:
        yield m

# Global fixture for rate limiting between tests
@pytest.fixture(scope="session", autouse=True)
def rate_limiter():
    """Add delay between tests to avoid hitting API rate limits."""
    start_time = time.time()
    yield
    end_time = time.time()
    elapsed = end_time - start_time
    if elapsed < 1.0:  # Add delay if test was too fast
        time.sleep(1.0 - elapsed)

# Fixture for API clients
@pytest.fixture(scope="module")
def api_clients():
    """Provide API clients for integration tests."""
    from app.alpha_vantage_client import AlphaVantageClient
    from app.finnhub_client import FinnhubClient
    from app.news_client import NewsAPIClient
    
    return {
        'alpha_vantage': AlphaVantageClient(),
        'finnhub': FinnhubClient(),
        'newsapi': NewsAPIClient()
    }
