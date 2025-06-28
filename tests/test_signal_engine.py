import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.signals.data_fetcher import fetch_ohlcv
from app.signals.engine import generate_signals

df = fetch_ohlcv("EURUSD")
signals_df = generate_signals(df)
print(signals_df[["close", "signal"]].tail())
