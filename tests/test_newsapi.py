import pytest
from unittest.mock import patch, MagicMock
from app.news_client import NewsAPIClient

def test_newsapi_client_initialization():
    """Test NewsAPI client initialization."""
    # Test with API key from environment
    client = NewsAPIClient(api_key="test_key")
    assert client.api_key == "test_key"
    
    # Test with no API key (should raise error)
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError):
            NewsAPIClient()

@patch('app.news_client.requests.Session')
def test_get_top_headlines(mock_session):
    """Test getting top headlines."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'status': 'ok',
        'totalResults': 1,
        'articles': [
            {
                'title': 'Test Article',
                'description': 'Test Description',
                'url': 'https://example.com/test'
            }
        ]
    }
    mock_session.return_value.get.return_value = mock_response
    
    # Test the function
    client = NewsAPIClient(api_key="test_key")
    articles = client.get_top_headlines(query="bitcoin")
    
    # Assertions
    assert len(articles) == 1
    assert articles[0]['title'] == 'Test Article'
    mock_session.return_value.get.assert_called_once()

@patch('app.news_client.requests.Session')
def test_get_everything(mock_session):
    """Test searching all articles."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'status': 'ok',
        'totalResults': 2,
        'articles': [
            {'title': 'Article 1', 'url': 'https://example.com/1'},
            {'title': 'Article 2', 'url': 'https://example.com/2'}
        ]
    }
    mock_session.return_value.get.return_value = mock_response
    
    # Test the function
    client = NewsAPIClient(api_key="test_key")
    articles = client.get_everything(query="ethereum")
    
    # Assertions
    assert len(articles) == 2
    assert all(article['title'].startswith('Article ') for article in articles)

@patch('app.news_client.requests.Session')
def test_error_handling(mock_session):
    """Test error handling in API requests."""
    # Setup mock to raise an exception
    mock_session.return_value.get.side_effect = Exception("API Error")
    
    client = NewsAPIClient(api_key="test_key")
    
    with pytest.raises(Exception) as excinfo:
        client.get_top_headlines()
    assert "API Error" in str(excinfo.value)

@patch('app.news_client.requests.Session')
def test_rate_limit_handling(mock_session):
    """Test rate limit handling."""
    # Setup mock to fail with 429 then succeed
    error_response = MagicMock()
    error_response.status_code = 429
    error_response.json.return_value = {'status': 'error', 'code': 'rateLimited', 'message': 'Rate limit reached'}
    
    success_response = MagicMock()
    success_response.json.return_value = {'status': 'ok', 'totalResults': 0, 'articles': []}
    
    mock_session.return_value.get.side_effect = [
        requests.exceptions.HTTPError("429 Client Error", response=error_response),
        success_response
    ]
    
    client = NewsAPIClient(api_key="test_key")
    articles = client.get_top_headlines()
    
    # Should have retried and eventually succeeded
    assert articles == []
    assert mock_session.return_value.get.call_count == 2
