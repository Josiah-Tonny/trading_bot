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
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = self.data['close'].rolling(period).mean()
        std = self.data['close'].rolling(period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, lower, sma

    def calculate_adx(self, period: int = 14) -> pd.Series:
        """Average Directional Index"""
        high = self.data['high']
        low = self.data['low']
        close = self.data['close']
        
        # Calculate True Range
        tr = pd.DataFrame(index=close.index)
        tr['h-l'] = high - low
        tr['h-pc'] = abs(high - close.shift())
        tr['l-pc'] = abs(low - close.shift())
        tr['tr'] = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        
        # Calculate Directional Movement
        up_move = high.diff()
        down_move = low.diff()
        
        dm_plus = pd.Series(np.where(
            (up_move > down_move) & (up_move > 0),
            up_move,
            0
        ))
        
        dm_minus = pd.Series(np.where(
            (down_move > up_move) & (down_move > 0),
            down_move,
            0
        ))
        
        # Calculate Smoothed Values
        tr_ewm = tr['tr'].ewm(span=period, adjust=False).mean()
        dm_plus_ewm = dm_plus.ewm(span=period, adjust=False).mean()
        dm_minus_ewm = dm_minus.ewm(span=period, adjust=False).mean()
        
        # Calculate Directional Indicators
        di_plus = (dm_plus_ewm / tr_ewm) * 100
        di_minus = (dm_minus_ewm / tr_ewm) * 100
        
        # Calculate ADX
        dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100
        adx = dx.ewm(span=period, adjust=False).mean()
        return adx

    def calculate_stochastic_oscillator(
        self, period: int = 14, k_period: int = 3, d_period: int = 3
    ) -> tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator"""
        high = self.data['high'].rolling(period).max()
        low = self.data['low'].rolling(period).min()
        k = ((self.data['close'] - low) / (high - low)) * 100
        k = k.rolling(k_period).mean()
        d = k.rolling(d_period).mean()
        return k, d

    # Signal Generation --------------------------------------------------------
    def generate_signal(
        self, capital: float = 10, risk_profile: str = "standard"
    ) -> Dict[str, Any]:
        """Generate trade signal with TP/SL and position size based on risk profile"""
        # Calculate indicators
        self.data['ema20'] = self.calculate_ema(20)
        self.data['ema50'] = self.calculate_ema(50)
        self.data['ema200'] = self.calculate_ema(200)
        macd_line, signal_line, hist = self.calculate_macd()
        self.data['rsi'] = self.calculate_rsi()
        self.data['adx'] = self.calculate_adx()
        k, d = self.calculate_stochastic_oscillator()
        self.data['stoch_k'] = k
        self.data['stoch_d'] = d
        self.data['atr'] = self.calculate_atr()
        upper_bb, lower_bb, bb_sma = self.calculate_bollinger_bands()
        
        # Get latest values
        current_close = self.data['close'].iloc[-1]
        current_rsi = self.data['rsi'].iloc[-1]
        current_adx = self.data['adx'].iloc[-1]
        current_stoch_k = self.data['stoch_k'].iloc[-1]
        current_stoch_d = self.data['stoch_d'].iloc[-1]
        current_atr = self.data['atr'].iloc[-1]
        
        # Get EMA values
        ema20 = self.data['ema20'].iloc[-1]
        ema50 = self.data['ema50'].iloc[-1]
        ema200 = self.data['ema200'].iloc[-1]
        
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
                'adx': round(current_adx, 2),
                'stoch_k': round(current_stoch_k, 2),
                'stoch_d': round(current_stoch_d, 2),
                'atr': round(current_atr, 5),
                'macd': round(macd_line.iloc[-1], 5)
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

        # Multiple confirmation points for buy signal
        buy_conditions = [
            # Trend confirmation
            current_close > ema20 and ema20 > ema50 and ema50 > ema200,
            # Momentum confirmation
            current_rsi > 30 and current_rsi < 70,
            current_stoch_k > 20 and current_stoch_k < 80,
            current_stoch_k > current_stoch_d,
            # Trend strength
            current_adx > 25,
            # Price above Bollinger Bands
            current_close > bb_sma
        ]
        
        # Multiple confirmation points for sell signal
        sell_conditions = [
            # Trend confirmation
            current_close < ema20 and ema20 < ema50 and ema50 < ema200,
            # Momentum confirmation
            current_rsi > 30 and current_rsi < 70,
            current_stoch_k > 20 and current_stoch_k < 80,
            current_stoch_k < current_stoch_d,
            # Trend strength
            current_adx > 25,
            # Price below Bollinger Bands
            current_close < bb_sma
        ]

        # Generate signals with multiple confirmations
        if all(buy_conditions):
            signal['action'] = 'buy'
            signal['sl'] = current_close - (current_atr * sl_mult)
            signal['tp'] = [
                current_close + (current_atr * tp_mults[0]),
                current_close + (current_atr * tp_mults[1]),
                current_close + (current_atr * tp_mults[2])
            ]
            # Calculate confidence based on multiple factors
            confidence = 0
            if current_rsi > 50: confidence += 20
            if current_stoch_k > 50: confidence += 20
            if current_adx > 25: confidence += 20
            if current_close > ema20: confidence += 20
            if current_close > ema50: confidence += 20
            signal['confidence'] = min(100, confidence)
        elif all(sell_conditions):
            signal['action'] = 'sell'
            signal['sl'] = current_close + (current_atr * sl_mult)
            signal['tp'] = [
                current_close - (current_atr * tp_mults[0]),
                current_close - (current_atr * tp_mults[1]),
                current_close - (current_atr * tp_mults[2])
            ]
            # Calculate confidence based on multiple factors
            confidence = 0
            if current_rsi < 50: confidence += 20
            if current_stoch_k < 50: confidence += 20
            if current_adx > 25: confidence += 20
            if current_close < ema20: confidence += 20
            if current_close < ema50: confidence += 20
            signal['confidence'] = min(100, confidence)

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