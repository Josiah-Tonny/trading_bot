import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ALPHAVANTAGE_KEY = os.getenv("ALPHAVANTAGE_KEY")

def fetch_ohlc_data(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Fetch OHLC data for the given symbol and timeframe from Alpha Vantage.
    Returns a pandas DataFrame with columns: ['open', 'high', 'low', 'close', 'volume'].
    """
    # Map timeframe to Alpha Vantage interval
    tf_map = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "60min",
        "4h": "60min",  # Alpha Vantage does not support 4h directly
        "1d": "Daily"
    }
    interval = tf_map.get(timeframe, "15min")
    if timeframe == "1d":
        function = "TIME_SERIES_DAILY"
        url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={ALPHAVANTAGE_KEY}&outputsize=compact"
        key = "Time Series (Daily)"
    else:
        function = "TIME_SERIES_INTRADAY"
        url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval={interval}&apikey={ALPHAVANTAGE_KEY}&outputsize=compact"
        key = f"Time Series ({interval})"

    resp = requests.get(url)
    data = resp.json()
    if key not in data:
        raise Exception(f"Alpha Vantage error: {data.get('Note') or data.get('Error Message') or 'Unknown error'}")
    df = pd.DataFrame.from_dict(data[key], orient="index")
    df = df.rename(columns=lambda x: x.split(". ")[1])
    df = df.astype(float)
    df = df.rename(columns={"open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df
