# engine.py
import ta
import pandas as pd

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate trading signals based on EMA, MACD, and RSI indicators.
    Returns the DataFrame with a new 'signal' column.
    """
    df = df.copy()
    df["ema_fast"] = ta.trend.EMAIndicator(df["close"], window=12).ema_indicator()
    df["ema_slow"] = ta.trend.EMAIndicator(df["close"], window=26).ema_indicator()
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    df["signal"] = None
    df.loc[
        (df["ema_fast"] > df["ema_slow"]) &
        (df["macd"] > df["macd_signal"]) &
        (df["rsi"] < 30),
        "signal"
    ] = "buy"
    df.loc[
        (df["ema_fast"] < df["ema_slow"]) &
        (df["macd"] < df["macd_signal"]) &
        (df["rsi"] > 70),
        "signal"
    ] = "sell"

    return df