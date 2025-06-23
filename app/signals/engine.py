# engine.py
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union
from app.data_fetcher import fetch_ohlc_data
from app.risk_manager import calculate_position_size
from app.utils import timeframes, logger

class SignalEngine:
    def __init__(self, symbol: str, timeframe: str) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = self._fetch_and_preprocess_data()

    def _fetch_and_preprocess_data(self) -> pd.DataFrame:
        """Fetch and prepare OHLC data"""
        df = fetch_ohlc_data(self.symbol, self.timeframe)
        df = self._clean_data(df)
        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values and outliers"""
        df.replace(0, np.nan, inplace=True)
        df.ffill(inplace=True)
        df.bfill(inplace=True)
        return df

    # Technical Indicators ------------------------------------------------------
    def calculate_ema(self, period: int = 20) -> pd.Series:
        """Exponential Moving Average"""
        return self.data['close'].ewm(span=period, adjust=False).mean()

    def calculate_macd(
        self, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """MACD with Signal Line"""
        ema_fast = self.data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.data['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_atr(self, period: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = self.data['high'] - self.data['low']
        high_close = np.abs(self.data['high'] - self.data['close'].shift())
        low_close = np.abs(self.data['low'] - self.data['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(period).mean()

    def calculate_bollinger_bands(
        self, period: int = 20, num_std: int = 2
    ) -> tuple[pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = self.data['close'].rolling(period).mean()
        std = self.data['close'].rolling(period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, lower

    # Signal Generation --------------------------------------------------------
    def generate_signal(
        self, capital: float = 10, risk_profile: str = "standard"
    ) -> Dict[str, Any]:
        """Generate trade signal with TP/SL and position size based on risk profile"""
        # Calculate indicators
        self.data['ema20'] = self.calculate_ema(20)
        macd_line, signal_line, hist = self.calculate_macd()
        self.data['rsi'] = self.calculate_rsi()
        self.data['atr'] = self.calculate_atr()
        
        # Get latest values
        current_close = self.data['close'].iloc[-1]
        current_rsi = self.data['rsi'].iloc[-1]
        current_atr = self.data['atr'].iloc[-1]
        prev_macd = macd_line.iloc[-2]
        current_macd = macd_line.iloc[-1]
        prev_signal = signal_line.iloc[-2]
        current_signal = signal_line.iloc[-1]
        
        # Initialize signal
        signal = {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'action': 'hold',
            'entry': current_close,
            'tp': [],
            'sl': 0,
            'confidence': 0,
            'timestamp': pd.Timestamp.now(),
            'indicators': {
                'rsi': round(current_rsi, 2),
                'atr': round(current_atr, 5),
                'macd': round(current_macd, 5)
            }
        }
        
        # Risk profile logic
        risk_map = {
            "conservative": 0.5,
            "standard": 1,
            "aggressive": 2
        }
        risk_percent = risk_map.get(risk_profile, 1)

        # TP/SL multipliers by timeframe
        tf = self.timeframe.lower()
        if tf in ["5m", "5min"]:
            tp_mults = [1, 1.5, 2]
            sl_mult = 1
        elif tf in ["15m", "15min"]:
            tp_mults = [1.5, 2, 2.5]
            sl_mult = 1.2
        elif tf in ["4h", "4hr"]:
            tp_mults = [2, 3, 4]
            sl_mult = 1.5
        elif tf in ["24h", "1d", "daily"]:
            tp_mults = [3, 4, 5]
            sl_mult = 2
        else:
            tp_mults = [1, 2, 3]
            sl_mult = 1

        # MACD crossover strategy
        bull_crossover = (prev_macd < prev_signal) and (current_macd > current_signal)
        bear_crossover = (prev_macd > prev_signal) and (current_macd < current_signal)

        # Generate signals
        if bull_crossover and current_rsi < 65:
            signal['action'] = 'buy'
            signal['sl'] = current_close - (current_atr * sl_mult)
            signal['tp'] = [
                current_close + (current_atr * tp_mults[0]),
                current_close + (current_atr * tp_mults[1]),
                current_close + (current_atr * tp_mults[2])
            ]
            signal['confidence'] = min(90, 70 + (30 - current_rsi)/2)
        elif bear_crossover and current_rsi > 35:
            signal['action'] = 'sell'
            signal['sl'] = current_close + (current_atr * sl_mult)
            signal['tp'] = [
                current_close - (current_atr * tp_mults[0]),
                current_close - (current_atr * tp_mults[1]),
                current_close - (current_atr * tp_mults[2])
            ]
            signal['confidence'] = min(90, 70 + (current_rsi - 70)/2)

        # Add position sizing
        if signal['action'] != 'hold':
            signal.update(calculate_position_size(
                capital=capital,
                entry=signal['entry'],
                stop_loss=signal['sl'],
                risk_percent=risk_percent
            ))

        return signal

    def backtest_strategy(
        self, capital: float = 10, risk_percent: float = 1
    ) -> None:
        """Backtest strategy on historical data"""
        # ...implementation would go here...
        pass

# Utility Functions -----------------------------------------------------------
def generate_daily_signals(user: Any) -> List[Dict[str, Any]]:
    """Generate signals for user's subscribed symbols/timeframes and risk profile"""
    signals: List[Dict[str, Any]] = []
    for sub in user.subscriptions:
        for symbol in sub.symbols:
            for timeframe in sub.timeframes:
                try:
                    # Use user or subscription risk profile if available
                    risk_profile = getattr(sub, "risk_profile", getattr(user, "risk_profile", "standard"))
                    engine = SignalEngine(symbol, timeframe)
                    signal = engine.generate_signal(capital=sub.capital, risk_profile=risk_profile)
                    if signal['action'] != 'hold':
                        signals.append(signal)
                except Exception as e:
                    logger.error(f"Signal error for {symbol}/{timeframe}: {str(e)}")
    # Return max 3 highest confidence signals
    return sorted(signals, key=lambda x: x['confidence'], reverse=True)[:3]