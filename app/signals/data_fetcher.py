# data_fetcher.py
import pandas as pd

def fetch_ohlcv(symbol: str, interval: str = "15m", limit: int = 100) -> pd.DataFrame:
    """
    Fetch OHLCV data for a given symbol and interval.
    This is a stub. Replace with actual API call (e.g., yfinance, Alpha Vantage, etc.).
    """
    # Example: return a dummy DataFrame
    data = {
        "open": [1.0] * limit,
        "high": [1.1] * limit,
        "low": [0.9] * limit,
        "close": [1.05] * limit,
        "volume": [100] * limit,
    }
    df = pd.DataFrame(data)
    return df