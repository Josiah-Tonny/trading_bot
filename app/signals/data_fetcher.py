# data_fetcher.py
import pandas as pd

def fetch_ohlc_data(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Fetch OHLC data for the given symbol and timeframe.
    Returns a pandas DataFrame with columns: ['open', 'high', 'low', 'close', 'volume'].
    """
    # Implement API call here (e.g., Alpha Vantage, Yahoo Finance)
    # For now, return a dummy DataFrame for testing
    return pd.DataFrame({
        'open': [1, 2, 3],
        'high': [2, 3, 4],
        'low': [0.5, 1.5, 2.5],
        'close': [1.5, 2.5, 3.5],
        'volume': [100, 150, 120]
    })