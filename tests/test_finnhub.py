import pytest
import requests
from unittest.mock import patch, MagicMock
from app.finnhub_client import FinnhubClient

def test_finnhub_client_initialization():
    """Test Finnhub client initialization."""
    # Test with API key from environment
    client = FinnhubClient(api_key="test_key")
    assert client.api_key == "test_key"
    
    # Test with no API key (should raise error)
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError):
            FinnhubClient()

@patch('app.finnhub_client.requests.Session')
def test_get_quote(mock_session):
    """Test getting a stock quote."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'c': 150.0, 'h': 151.0, 'l': 149.0, 
        'o': 150.5, 'pc': 148.5, 't': 1617187200
    }
    mock_session.return_value.get.return_value = mock_response
    
    # Test the function
    client = FinnhubClient(api_key="test_key")
    quote = client.get_quote("AAPL")
    
    # Assertions
    assert 'c' in quote
    assert quote['c'] == 150.0
    mock_session.return_value.get.assert_called_once_with(
        "https://finnhub.io/api/v1/quote?symbol=AAPL",
        params={'token': 'test_key'},
        timeout=10
    )

@patch('app.finnhub_client.requests.Session')
def test_error_handling(mock_session):
    """Test error handling in API requests."""
    # Setup mock to raise an exception
    mock_session.return_value.get.side_effect = requests.exceptions.RequestException("API Error")
    
    client = FinnhubClient(api_key="test_key")
    
    with pytest.raises(Exception) as excinfo:
        client.get_quote("AAPL")
    assert "API Error" in str(excinfo.value)

def test_retry_logic(mocker):
    """Test that retry logic works on failed requests."""
    # Setup mock to fail twice then succeed
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {'c': 150.0}
    
    # Create a mock session with side effects
    mock_session = mocker.patch('app.finnhub_client.requests.Session')
    
    # Create a mock HTTP error
    error_response = mocker.MagicMock()
    error_response.status_code = 500
    http_error = requests.exceptions.HTTPError(response=error_response)
    
    mock_session.return_value.get.side_effect = [
        http_error,
        http_error,
        mock_response
    ]
    
    # Patch the sleep function to speed up the test
    mocker.patch('time.sleep')
    
    client = FinnhubClient(api_key="test_key")
    
    # This should succeed after two retries
    quote = client.get_quote("AAPL")
    assert quote['c'] == 150.0
    
    # Verify the request was retried 3 times (initial + 2 retries)
    assert mock_session.return_value.get.call_count == 3
