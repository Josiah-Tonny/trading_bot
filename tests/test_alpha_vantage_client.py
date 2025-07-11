import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import requests
from app.alpha_vantage_client import AlphaVantageClient

# Fixtures
@pytest.fixture
def mock_alpha_vantage_response():
    """Mock response for Alpha Vantage API."""
    return {
        "Meta Data": {
            "1. Information": "Intraday (5min) open, high, low, close prices and volume",
            "2. Symbol": "AAPL",
            "3. Last Refreshed": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "4. Interval": "5min",
            "5. Output Size": "Compact",
            "6. Time Zone": "US/Eastern"
        },
        "Time Series (5min)": {
            (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'): {
                "1. open": "150.0000",
                "2. high": "151.0000",
                "3. low": "149.5000",
                "4. close": "150.5000",
                "5. volume": "1000"
            },
            (datetime.now() - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S'): {
                "1. open": "149.5000",
                "2. high": "150.5000",
                "3. low": "149.0000",
                "4. close": "150.0000",
                "5. volume": "800"
            }
        }
    }

@pytest.fixture
def mock_daily_alpha_vantage_response():
    """Mock daily response for Alpha Vantage API."""
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "AAPL",
            "3. Last Refreshed": datetime.now().strftime('%Y-%m-%d'),
            "4. Output Size": "Compact",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": {
            (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'): {
                "1. open": "152.0000",
                "2. high": "153.0000",
                "3. low": "151.5000",
                "4. close": "152.5000",
                "5. volume": "5000"
            },
            (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'): {
                "1. open": "151.0000",
                "2. high": "152.5000",
                "3. low": "150.5000",
                "4. close": "152.0000",
                "5. volume": "4500"
            }
        }
    }

def test_alpha_vantage_client_initialization():
    """Test AlphaVantage client initialization."""
    # Test with API key from environment
    client = AlphaVantageClient(api_key="test_key")
    assert client.api_key == "test_key"
    
    # Test with no API key (should raise error)
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError):
            AlphaVantageClient()

@patch('app.alpha_vantage_client.requests.Session')
def test_get_ohlc_data_intraday(mock_session, mock_alpha_vantage_response):
    """Test get_ohlc_data method for intraday data."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = mock_alpha_vantage_response
    mock_session.return_value.get.return_value = mock_response
    
    # Test the client
    client = AlphaVantageClient(api_key="test_key")
    df = client.get_ohlc_data("AAPL", "5m")
    
    # Assertions
    assert not df.empty
    assert len(df) == 2  # Should have 2 data points
    assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
    assert df.index.is_monotonic_increasing

@patch('app.alpha_vantage_client.requests.Session')
def test_get_ohlc_data_daily(mock_session, mock_daily_alpha_vantage_response):
    """Test get_ohlc_data method for daily data."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = mock_daily_alpha_vantage_response
    mock_session.return_value.get.return_value = mock_response
    
    # Test the client
    client = AlphaVantageClient(api_key="test_key")
    df = client.get_ohlc_data("AAPL", "1d")
    
    # Assertions
    assert not df.empty
    assert len(df) == 2  # Should have 2 data points
    assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
    assert df.index.is_monotonic_increasing

def test_get_ohlc_data_invalid_timeframe():
    """Test get_ohlc_data with invalid timeframe."""
    client = AlphaVantageClient(api_key="test_key")
    with pytest.raises(ValueError, match="Unsupported timeframe"):
        client.get_ohlc_data("AAPL", "invalid_timeframe")

@patch('app.alpha_vantage_client.requests.Session')
def test_network_error_handling(mock_session):
    """Test network error handling in the client."""
    # Setup mock to raise a network error
    mock_session.return_value.get.side_effect = requests.exceptions.RequestException("Network error")
    
    client = AlphaVantageClient(api_key="test_key")
    
    # Test that the correct exception is raised
    with pytest.raises(ValueError) as excinfo:
        client.get_ohlc_data("AAPL", "5m")
    
    # Check that the error message is as expected
    assert "Failed to get OHLC data: Request failed: Network error" in str(excinfo.value)

@patch('app.alpha_vantage_client.requests.Session')
def test_api_error_handling(mock_session):
    """Test API error handling in the client."""
    # Setup mock response with API error
    mock_response = MagicMock()
    mock_response.json.return_value = {"Error Message": "Invalid API call"}
    mock_session.return_value.get.return_value = mock_response
    
    client = AlphaVantageClient(api_key="test_key")
    
    # Test that the correct exception is raised
    with pytest.raises(ValueError) as excinfo:
        client.get_ohlc_data("INVALID", "5m")
    
    # Check that the error message is as expected
    expected_error = "Failed to get OHLC data: Failed to parse API response: API Error: Invalid API call"
    assert expected_error in str(excinfo.value)
