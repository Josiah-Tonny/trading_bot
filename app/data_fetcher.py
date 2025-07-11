import pandas as pd
from .alpha_vantage_client import alpha_vantage_client

def fetch_ohlc_data(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Fetch OHLC data for the given symbol and timeframe using Alpha Vantage.
    
    Args:
        symbol: The stock symbol to fetch data for
        timeframe: The timeframe to fetch data for (1m, 5m, 15m, 30m, 1h, 1d)
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data
    """
    return alpha_vantage_client.get_ohlc_data(symbol, timeframe)
