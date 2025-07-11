import pytest
import pandas as pd
from datetime import datetime, timedelta
from app.data_fetcher import fetch_ohlc_data

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

class TestDataFetcherIntegration:
    """Integration tests for the data fetcher module."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Add delay between tests to avoid rate limiting
        import time
        time.sleep(1)
    
    @pytest.mark.parametrize("timeframe", ["1d", "4h", "1h", "15m"])
    def test_fetch_ohlc_data(self, timeframe):
        """Test fetching OHLC data for different timeframes."""
        print(f"\nTesting OHLC data fetch for {timeframe} timeframe...")
        
        # Test with a popular symbol
        symbol = "AAPL"
        df = fetch_ohlc_data(symbol, timeframe)
        
        # Print some data for visibility
        print(f"Fetched {len(df)} rows of {timeframe} data for {symbol}")
        if not df.empty:
            print(f"Latest data point: {df.index[0]}")
            print(f"Latest close: {df['close'].iloc[0]:.2f}")
        
        # Validate the response
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        assert all(col in df.columns for col in required_columns)
        assert df.index.is_monotonic_increasing
        
        # Check that the most recent date is recent
        most_recent = df.index.max()
        now = datetime.now()
        
        if timeframe == "1d":
            max_days_old = 7
            assert (now.date() - most_recent.date()) <= timedelta(days=max_days_old)
        else:
            # For intraday timeframes, data should be from today
            assert most_recent.date() == now.date()
    
    @pytest.mark.slow
    def test_end_to_end_workflow(self):
        """Test a complete workflow using the data fetcher."""
        print("\nRunning end-to-end workflow test...")
        
        # Test with a popular stock
        symbol = "MSFT"
        
        # 1. Get OHLC data
        print("1. Fetching OHLC data...")
        ohlc_data = fetch_ohlc_data(symbol, "1d")
        assert not ohlc_data.empty
        print(f"Fetched {len(ohlc_data)} days of OHLC data")
        
        # 2. Print a summary
        print("\n--- Workflow Summary ---")
        print(f"Symbol: {symbol}")
        print(f"Latest Close: {ohlc_data['close'].iloc[0]:.2f}")
        print(f"24h Change: {((ohlc_data['close'].iloc[0] / ohlc_data['close'].iloc[1]) - 1) * 100:.2f}%")
        
        print("\nWorkflow test completed successfully!")