import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.data_fetcher import fetch_ohlc_data
from app.alpha_vantage_client import AlphaVantageClient

class TestAlphaVantageIntegration:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, requests_mock):
        """Setup common mocks for all tests."""
        self.requests_mock = requests_mock
        self.api_key = "test_alpha_vantage_key"
        self.symbol = "AAPL"
        
        # Mock environment variables
        self.patcher = patch.dict('os.environ', {
            'ALPHA_VANTAGE_API_KEY': self.api_key,
            'FINNHUB_KEY': 'test_finnhub_key',
            'NEWSAPI_KEY': 'test_newsapi_key'
        })
        self.patcher.start()
        
        # Create a test client instance
        self.client = AlphaVantageClient(api_key=self.api_key)
        
        yield
        
        # Cleanup
        self.patcher.stop()

    def mock_alpha_vantage_response(self, interval="1min", is_daily=False):
        """Helper to create mock responses."""
        if is_daily:
            return {
                "Time Series (Daily)": {
                    "2023-01-01": {
                        "1. open": "100.0", "2. high": "101.0", 
                        "3. low": "99.0", "4. close": "100.5", 
                        "5. volume": "1000"
                    }
                }
            }
        return {
            f"Time Series ({interval})": {
                "2023-01-01 00:00:00": {
                    "1. open": "100.0", "2. high": "101.0", 
                    "3. low": "99.0", "4. close": "100.5", 
                    "5. volume": "1000"
                }
            }
        }

    @pytest.mark.parametrize("timeframe,expected_interval", [
        ("1m", "1min"),
        ("5m", "5min"),
        ("15m", "15min"),
        ("1h", "60min"),
        ("1d", "Daily"),
    ])
    def test_timeframe_mapping(self, timeframe, expected_interval):
        """Test that timeframes are correctly mapped to Alpha Vantage intervals."""
        is_daily = expected_interval == "Daily"
        mock_data = self.mock_alpha_vantage_response(
            interval=expected_interval,
            is_daily=is_daily
        )
        
        if is_daily:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={self.symbol}&apikey={self.api_key}&outputsize=compact&datatype=json"
        else:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={self.symbol}&interval={expected_interval}&apikey={self.api_key}&outputsize=compact&datatype=json"
        
        self.requests_mock.get(url, json=mock_data, status_code=200)
        
        # Test the function
        df = self.client.get_ohlc_data(self.symbol, timeframe)
        
        # Assertions
        assert not df.empty
        assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        assert df.index[0] == (pd.Timestamp("2023-01-01 00:00:00") if not is_daily else pd.Timestamp("2023-01-01"))

    def test_error_handling(self):
        """Test error handling for API responses."""
        symbol = "INVALID"
        error_message = {
            "Error Message": "Invalid API call. Please retry or visit the documentation."
        }
        
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_key}&outputsize=compact&datatype=json"
        self.requests_mock.get(url, json=error_message, status_code=200)
        
        with pytest.raises(ValueError) as excinfo:
            self.client.get_ohlc_data(symbol, "1d")
        
        assert "Failed to parse API response" in str(excinfo.value)
        assert "Invalid API call" in str(excinfo.value)

    def test_rate_limit_handling(self):
        """Test rate limit handling."""
        rate_limit_message = {
            "Note": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."
        }
        
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={self.symbol}&apikey={self.api_key}&outputsize=compact&datatype=json"
        self.requests_mock.get(url, json=rate_limit_message, status_code=200)
        
        with pytest.raises(ValueError) as excinfo:
            self.client.get_ohlc_data(self.symbol, "1d")
        
        assert "rate limit" in str(excinfo.value).lower()
