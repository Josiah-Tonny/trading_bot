import pytest
import pandas as pd
from datetime import datetime
from app.signals.data_fetcher import fetch_ohlc_data

class TestSignalEngine:
    """Tests for the signal engine module."""
    
    def test_fetch_ohlc_data(self):
        """Test fetching OHLC data from the signals module."""
        # Test with a popular symbol
        symbol = "AAPL"
        df = fetch_ohlc_data(symbol, "1d")
        
        # Basic validation
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        assert all(col in df.columns for col in required_columns)
        
        # Check index is datetime
        assert pd.api.types.is_datetime64_any_dtype(df.index)
        
        # Check data types
        for col in required_columns:
            assert pd.api.types.is_numeric_dtype(df[col])
    
    @pytest.mark.parametrize("timeframe", ["1d", "4h", "1h", "15m"])
    def test_fetch_ohlc_data_timeframes(self, timeframe):
        """Test fetching OHLC data with different timeframes."""
        symbol = "MSFT"
        df = fetch_ohlc_data(symbol, timeframe)
        
        assert not df.empty
        assert len(df) > 0
        assert df.index.is_monotonic_increasing