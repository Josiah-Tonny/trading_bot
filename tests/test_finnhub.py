import pytest
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
    mock_session.return_value.get.side_effect = Exception("API Error")
    
    client = FinnhubClient(api_key="test_key")
    
    with pytest.raises(Exception) as excinfo:
        client.get_quote("AAPL")
    assert "API Error" in str(excinfo.value)

@patch('app.finnhub_client.requests.Session')
def test_retry_logic(mock_session):
    """Test that retry logic works on failed requests."""
    # Setup mock to fail twice then succeed
    mock_response = MagicMock()
    mock_response.json.return_value = {'c': 150.0}
    
    mock_session.return_value.get.side_effect = [
        Exception("First failure"),
        Exception("Second failure"),
        mock_response
    ]
    
    client = FinnhubClient(api_key="test_key")
    quote = client.get_quote("AAPL")
    
    # Should have retried and eventually succeeded
    assert quote['c'] == 150.0
    assert mock_session.return_value.get.call_count == 3
