# data_fetcher.py
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta

def fetch_ohlc_data(symbol: str, timeframe: str, days: int = 30) -> Optional[pd.DataFrame]:
    """
    Fetch OHLC (Open, High, Low, Close) data for a given symbol and timeframe.
    
    This is a placeholder function that returns mock data. In a real implementation,
    it would fetch data from a data provider like Alpha Vantage, Yahoo Finance, etc.
    
    Args:
        symbol: The trading symbol (e.g., 'AAPL')
        timeframe: The timeframe for the data (e.g., '5m', '1h', '1d')
        days: Number of days of historical data to return (default: 30)
        
    Returns:
        A pandas DataFrame with OHLC data and volume, indexed by datetime.
        Returns None if data cannot be fetched.
    """
    try:
        # This is mock data - in a real implementation, you would fetch from an API
        now = datetime.now()
        date_range = pd.date_range(end=now, periods=days, freq='D')
        
        # Generate some random price data
        np.random.seed(42)  # For reproducibility
        base_prices = 100 + np.cumsum(np.random.randn(len(date_range)) * 2)
        
        # Create DataFrame with OHLC data
        data = {
            'open': base_prices * 0.99,
            'high': base_prices * 1.02,
            'low': base_prices * 0.98,
            'close': base_prices,
            'volume': np.random.randint(1000, 10000, size=len(date_range))
        }
        
        df = pd.DataFrame(data, index=date_range)
        
        # Ensure the index is timezone-naive (or set to UTC if your data is timezone-aware)
        df.index = df.index.tz_localize(None)
        
        # Sort by datetime (oldest first)
        df = df.sort_index()
        
        return df
        
    except Exception as e:
        print(f"Error fetching OHLC data for {symbol} ({timeframe}): {str(e)}")
        return None