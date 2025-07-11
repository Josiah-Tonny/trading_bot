import pytest
import pandas as pd
from app.data_fetcher import fetch_ohlc_data

class TestAlphaVantageIntegration:
    @pytest.mark.parametrize("timeframe,expected_interval", [
        ("1m", "1min"),
        ("5m", "5min"),
        ("15m", "15min"),
        ("1h", "60min"),
        ("1d", "Daily"),
    ])
    def test_timeframe_mapping(self, requests_mock, timeframe, expected_interval):
        """Test that timeframes are correctly mapped to Alpha Vantage intervals."""
        symbol = "AAPL"
        mock_response = {
            f"Time Series ({expected_interval})": {
                "2023-01-01 00:00:00": {
                    "1. open": "100.0", "2. high": "101.0", 
                    "3. low": "99.0", "4. close": "100.5", "5. volume": "1000"
                }
            }
        }
        
        if expected_interval == "Daily":
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey=test_alpha_vantage_key&outputsize=compact"
        else:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={expected_interval}&apikey=test_alpha_vantage_key&outputsize=compact"
        
        requests_mock.get(url, json=mock_response)
        
        # Test the function
        df = fetch_ohlc_data(symbol, timeframe)
        
        # Assertions
        assert not df.empty
        assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        assert df.index[0] == pd.Timestamp("2023-01-01")

    def test_error_handling(self, requests_mock):
        """Test error handling for API responses."""
        symbol = "INVALID"
        error_message = {"Error Message": "Invalid API call. Please retry or visit the documentation."}
        
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey=test_alpha_vantage_key&outputsize=compact"
        requests_mock.get(url, json=error_message, status_code=200)
        
        with pytest.raises(Exception) as excinfo:
            fetch_ohlc_data(symbol, "1d")
        assert "Invalid API call" in str(excinfo.value)

    def test_rate_limit_handling(self, requests_mock):
        """Test rate limit handling."""
        symbol = "AAPL"
        rate_limit_message = {"Note": "Thank you for using Alpha Vantage!"}
        
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey=test_alpha_vantage_key&outputsize=compact"
        requests_mock.get(url, json=rate_limit_message, status_code=200)
        
        with pytest.raises(Exception) as excinfo:
            fetch_ohlc_data(symbol, "1d")
        assert "rate limit" in str(excinfo.value).lower()
