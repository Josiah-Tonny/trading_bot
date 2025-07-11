import os
import pytest
from dotenv import load_dotenv
import json
from pathlib import Path

# Load environment variables for testing
load_dotenv()

def load_mock_response(filename):
    """Helper to load mock API responses from JSON files."""
    test_dir = Path(__file__).parent / 'test_data'
    with open(test_dir / f'{filename}.json') as f:
        return json.load(f)

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv('ALPHAVANTAGE_KEY', 'test_alpha_vantage_key')
    monkeypatch.setenv('FINNHUB_KEY', 'test_finnhub_key')
    monkeypatch.setenv('NEWSAPI_KEY', 'test_newsapi_key')

@pytest.fixture
def mock_alpha_vantage_response():
    """Return a sample Alpha Vantage API response."""
    return {
        "Meta Data": {
            "1. Information": "Intraday (5min) open, high, low, close prices and volume",
            "2. Symbol": "AAPL",
            "3. Last Refreshed": "2023-01-01 19:55:00",
            "4. Interval": "5min",
            "5. Output Size": "Compact",
            "6. Time Zone": "US/Eastern"
        },
        "Time Series (5min)": {
            "2023-01-01 19:55:00": {
                "1. open": "150.0000",
                "2. high": "151.0000",
                "3. low": "149.5000",
                "4. close": "150.5000",
                "5. volume": "1000"
            }
        }
    }
