# engine.py
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union
from app.data_fetcher import fetch_ohlc_data
from app.risk_manager import calculate_position_size
from app.utils import timeframes, logger

class SignalEngine:
    def __init__(self, symbol: str, timeframe: str, subscription_tier: SubscriptionTier) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.tier = subscription_tier
        self.data = self._fetch_and_preprocess_data()
        
        # Initialize advanced features based on tier
        self._setup_tier_features()

    def _setup_tier_features(self) -> None:
        """Configure available features based on subscription tier"""
        self.features = self.tier.features
        self.limits = self.tier.signal_limits
        
        # Enable/disable advanced indicators
        self.use_advanced_indicators = self.features.get('advanced_signals', False)
        self.use_portfolio_optimization = self.features.get('portfolio_optimization', False)
        self.use_risk_analysis = self.features.get('risk_analysis', False)

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
    def calculate_sma(self, period: int = 20) -> pd.Series:
        """Simple Moving Average"""
        return self.data['close'].rolling(window=period).mean()

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

    def calculate_adx(self, period: int = 14) -> tuple[pd.Series, pd.Series, pd.Series]:
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
        return adx, di_plus, di_minus

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

    def calculate_bollinger_bands(
        self, period: int = 20, num_std: int = 2
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = self.data['close'].rolling(period).mean()
        std = self.data['close'].rolling(period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, lower, sma

    def calculate_standard_deviation(self, period: int = 20) -> pd.Series:
        """Standard Deviation"""
        return self.data['close'].rolling(window=period).std()

    def calculate_fibonacci_retracements(
        self, high: float, low: float
    ) -> Dict[str, float]:
        """Calculate Fibonacci Retracement Levels"""
        levels = {}
        range = high - low
        
        # Common Fibonacci levels
        fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        
        for level in fib_levels:
            levels[f'fib_{int(level*100)}'] = high - (range * level)
            
        # Add 100% level (low point)
        levels['fib_100'] = low
        
        return levels

    def calculate_ichimoku_cloud(
        self, conversion_period: int = 9,
        base_period: int = 26,
        span_b_period: int = 52
    ) -> Dict[str, pd.Series]:
        """Ichimoku Cloud"""
        high = self.data['high']
        low = self.data['low']
        close = self.data['close']
        
        # Conversion Line (Tenkan-sen)
        conversion_line = (high.rolling(conversion_period).max() + 
                         low.rolling(conversion_period).min()) / 2
        
        # Base Line (Kijun-sen)
        base_line = (high.rolling(base_period).max() + 
                    low.rolling(base_period).min()) / 2
        
        # Leading Span A
        span_a = (conversion_line + base_line) / 2
        
        # Leading Span B
        span_b = (high.rolling(span_b_period).max() + 
                 low.rolling(span_b_period).min()) / 2
        
        # Lagging Span
        lagging_span = close.shift(-base_period)
        
        return {
            'conversion_line': conversion_line,
            'base_line': base_line,
            'span_a': span_a,
            'span_b': span_b,
            'lagging_span': lagging_span
        }

    def calculate_volume_indicators(self) -> Dict[str, pd.Series]:
        """Volume-based indicators"""
        volume = self.data['volume']
        
        # VWAP (Volume Weighted Average Price)
        typical_price = (self.data['high'] + self.data['low'] + self.data['close']) / 3
        volume_typical = typical_price * volume
        vwap = volume_typical.cumsum() / volume.cumsum()
        
        # Volume Weighted Moving Average
        vwma = (volume * self.data['close']).rolling(window=14).sum() / \
               volume.rolling(window=14).sum()
        
        return {
            'vwap': vwap,
            'vwma': vwma
        }

    def calculate_atr(self, period: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = self.data['high'] - self.data['low']
        high_close = np.abs(self.data['high'] - self.data['close'].shift())
        low_close = np.abs(self.data['low'] - self.data['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(period).mean()

    # Signal Generation --------------------------------------------------------
    def generate_signal_with_permissions(
        self, capital: float = 10000, risk_profile: str = "standard"
    ) -> SignalResult:
        """Generate signals with tier-appropriate analysis"""
        base_signal = self._generate_base_signal(capital, risk_profile)
        permissions = self._get_permissions()
        
        if self.use_advanced_indicators:
            advanced = self._generate_advanced_analysis()
        else:
            advanced = None
            
        return {
            "signal": base_signal,
            "permissions": permissions,
            "advanced_analysis": advanced
        }

    def _get_permissions(self) -> SignalPermissions:
        """Get current signal permissions based on subscription tier"""
        return {
            "custom_signals_remaining": self.limits['custom_signals'],
            "allowed_timeframes": self.limits['timeframes'],
            "requests_remaining": self.limits['requests_per_hour'],
            "advanced_indicators": self.use_advanced_indicators,
            "portfolio_optimization": self.use_portfolio_optimization,
            "risk_analysis": self.use_risk_analysis
        }

    def _generate_base_signal(
        self, capital: float, risk_profile: str
    ) -> TradingSignal:
        """Generate basic trading signal with essential indicators"""
        # Calculate core indicators
        sma20 = self.data['close'].rolling(window=20).mean()
        sma50 = self.data['close'].rolling(window=50).mean()
        rsi = self.calculate_rsi()
        k, d = self.calculate_stochastic_oscillator()
        
        # Get current values
        current_close = self.data['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_k = k.iloc[-1]
        current_d = d.iloc[-1]
        
        # Generate signal components
        signal: TradingSignal = {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "action": "hold",  # Will be updated based on analysis
            "entry": current_close,
            "tp": [],  # Will be filled based on analysis
            "sl": 0,  # Will be updated based on ATR
            "confidence": 0,
            "timestamp": pd.Timestamp.now(),
            "indicators": self._get_indicators(),
            "trade_info": {
                "time_period": self.timeframe,
                "risk_profile": risk_profile,
                "market_conditions": self._get_market_conditions()
            }
        }
        
        # Add position sizing if signal generated
        signal = self._add_position_sizing(signal, capital, risk_profile)
        
        return signal

    def _get_indicators(self) -> SignalIndicators:
        """Get current values of all indicators"""
        return {
            "rsi": self.calculate_rsi().iloc[-1],
            "adx": self.calculate_adx()[0].iloc[-1],
            "stoch_k": self.calculate_stochastic_oscillator()[0].iloc[-1],
            "stoch_d": self.calculate_stochastic_oscillator()[1].iloc[-1],
            "atr": self.calculate_atr().iloc[-1],
            "std_dev": self.calculate_standard_deviation().iloc[-1],
            "macd": self.calculate_macd()[0].iloc[-1],
            "signal_line": self.calculate_macd()[1].iloc[-1],
            "histogram": self.calculate_macd()[2].iloc[-1]
        }

    def _generate_advanced_analysis(self) -> Dict[str, Any]:
        """Generate advanced analysis for pro/premium tiers"""
        if not self.use_advanced_indicators:
            return {}
            
        analysis = {}
        
        # Add portfolio optimization if available
        if self.use_portfolio_optimization:
            analysis["portfolio"] = self._get_portfolio_analysis()
            
        # Add risk analysis if available
        if self.use_risk_analysis:
            analysis["risk"] = self._get_risk_analysis()
            
        return analysis
        # Calculate all indicators
        self.data['sma20'] = self.calculate_sma(20)
        self.data['sma50'] = self.calculate_sma(50)
        self.data['sma200'] = self.calculate_sma(200)
        self.data['ema20'] = self.calculate_ema(20)
        self.data['ema50'] = self.calculate_ema(50)
        self.data['ema200'] = self.calculate_ema(200)
        
        macd_line, signal_line, hist = self.calculate_macd()
        self.data['rsi'] = self.calculate_rsi()
        adx, di_plus, di_minus = self.calculate_adx()
        k, d = self.calculate_stochastic_oscillator()
        upper_bb, lower_bb, bb_sma = self.calculate_bollinger_bands()
        std_dev = self.calculate_standard_deviation()
        
        # Get latest values
        current_close = self.data['close'].iloc[-1]
        current_rsi = self.data['rsi'].iloc[-1]
        current_adx = adx.iloc[-1]
        current_stoch_k = k.iloc[-1]
        current_stoch_d = d.iloc[-1]
        current_atr = self.calculate_atr().iloc[-1]
        current_std_dev = std_dev.iloc[-1]
        
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
                'std_dev': round(current_std_dev, 5),
                'macd': round(macd_line.iloc[-1], 5),
                'signal_line': round(signal_line.iloc[-1], 5),
                'histogram': round(hist.iloc[-1], 5)
            },
            'trade_info': {
                'time_period': self.timeframe,
                'trade_duration': self._get_trade_duration(),
                'market_conditions': self._get_market_conditions()
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
            signal['trade_info']['trade_duration'] = "5-15 minutes"
        elif tf in ["15m", "15min"]:
            tp_mults = [1.5, 2, 2.5]
            sl_mult = 1.2
            signal['trade_info']['trade_duration'] = "15-45 minutes"
        elif tf in ["4h", "4hr"]:
            tp_mults = [2, 3, 4]
            sl_mult = 1.5
            signal['trade_info']['trade_duration'] = "4-12 hours"
        elif tf in ["24h", "1d", "daily"]:
            tp_mults = [3, 4, 5]
            sl_mult = 2
            signal['trade_info']['trade_duration'] = "1-2 days"
        else:
            tp_mults = [1, 2, 3]
            sl_mult = 1
            signal['trade_info']['trade_duration'] = "1-3 hours"

        # Multiple confirmation points for buy signal
        buy_conditions = [
            # Trend confirmation (Multiple EMAs)
            current_close > ema20 and ema20 > ema50 and ema50 > ema200,
            # Momentum confirmation
            current_rsi > 30 and current_rsi < 70,
            current_stoch_k > 20 and current_stoch_k < 80,
            current_stoch_k > current_stoch_d,
            # Trend strength
            current_adx > 25,
            # Price above Bollinger Bands
            current_close > bb_sma,
            # MACD confirmation
            macd_line.iloc[-1] > signal_line.iloc[-1],
            # Volume confirmation
            self.data['volume'].iloc[-1] > self.data['volume'].rolling(10).mean().iloc[-1]
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
            current_close < bb_sma,
            # MACD confirmation
            macd_line.iloc[-1] < signal_line.iloc[-1],
            # Volume confirmation
            self.data['volume'].iloc[-1] > self.data['volume'].rolling(10).mean().iloc[-1]
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
            if current_rsi > 50: confidence += 10
            if current_stoch_k > 50: confidence += 10
            if current_adx > 40: confidence += 10
            if current_close > ema20: confidence += 10
            if current_close > ema50: confidence += 10
            if macd_line.iloc[-1] > signal_line.iloc[-1]: confidence += 10
            if current_std_dev > self.data['volume'].rolling(20).mean().iloc[-1]: confidence += 10
            signal['confidence'] = min(100, confidence)
            
            # Add trade explanation
            signal['trade_info']['explanation'] = self._explain_trade('buy', current_rsi, current_stoch_k, current_adx)
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
            if current_rsi < 50: confidence += 10
            if current_stoch_k < 50: confidence += 10
            if current_adx > 40: confidence += 10
            if current_close < ema20: confidence += 10
            if current_close < ema50: confidence += 10
            if macd_line.iloc[-1] < signal_line.iloc[-1]: confidence += 10
            if current_std_dev > self.data['volume'].rolling(20).mean().iloc[-1]: confidence += 10
            signal['confidence'] = min(100, confidence)
            
            # Add trade explanation
            signal['trade_info']['explanation'] = self._explain_trade('sell', current_rsi, current_stoch_k, current_adx)

        # Add position sizing
        if signal['action'] != 'hold':
            signal.update(calculate_position_size(
                capital=capital,
                entry=signal['entry'],
                stop_loss=signal['sl'],
                risk_percent=risk_percent
            ))

        return signal

    def _get_trade_duration(self) -> str:
        """Determine appropriate trade duration based on timeframe and market conditions"""
        # Get current timeframe
        tf = self.timeframe.lower()
        
        # Get market volatility
        current_std_dev = self.calculate_standard_deviation().iloc[-1]
        avg_std_dev = self.calculate_standard_deviation().rolling(20).mean().iloc[-1]
        volatility = "high" if current_std_dev > avg_std_dev * 1.5 else "low"
        
        # Get trend strength
        adx = self.calculate_adx()[0].iloc[-1]
        trend_strength = "strong" if adx > 40 else "weak"
        
        # Base durations by timeframe
        base_durations = {
            "5m": "5-15 minutes",
            "15m": "15-45 minutes",
            "4h": "4-12 hours",
            "1d": "1-2 days",
            "default": "1-3 hours"
        }
        
        # Adjust duration based on volatility and trend strength
        base_duration = base_durations.get(tf, base_durations["default"])
        
        if volatility == "high":
            if trend_strength == "strong":
                return f"{base_duration} (High volatility, strong trend - be cautious)"
            else:
                return f"{base_duration} (High volatility - consider shorter duration)"
        else:
            if trend_strength == "strong":
                return f"{base_duration} (Low volatility, strong trend - good conditions)"
            else:
                return f"{base_duration} (Low volatility, weak trend - caution advised)"

    def _get_market_conditions(self) -> str:
        """Analyze market conditions using multiple indicators"""
        # Calculate indicators
        adx, di_plus, di_minus = self.calculate_adx()
        rsi = self.calculate_rsi().iloc[-1]
        k, d = self.calculate_stochastic_oscillator()
        current_std_dev = self.calculate_standard_deviation().iloc[-1]
        
        # Get current values
        current_adx = adx.iloc[-1]
        current_stoch_k = k.iloc[-1]
        current_stoch_d = d.iloc[-1]
        
        # Analyze market conditions
        conditions = []
        
        # Trend analysis
        if current_adx > 40:
            if di_plus.iloc[-1] > di_minus.iloc[-1]:
                conditions.append("Strong uptrend")
            else:
                conditions.append("Strong downtrend")
        elif current_adx > 25:
            if di_plus.iloc[-1] > di_minus.iloc[-1]:
                conditions.append("Moderate uptrend")
            else:
                conditions.append("Moderate downtrend")
        else:
            conditions.append("Sideways market")
        
        # Momentum analysis
        if rsi > 70:
            conditions.append("Overbought")
        elif rsi < 30:
            conditions.append("Oversold")
        else:
            conditions.append("Neutral momentum")
        
        # Volatility analysis
        avg_std_dev = self.calculate_standard_deviation().rolling(20).mean().iloc[-1]
        if current_std_dev > avg_std_dev * 1.5:
            conditions.append("High volatility")
        elif current_std_dev < avg_std_dev * 0.8:
            conditions.append("Low volatility")
        else:
            conditions.append("Normal volatility")
        
        # Market strength analysis
        if current_stoch_k > 80 and current_stoch_d > 80:
            conditions.append("Strong buying pressure")
        elif current_stoch_k < 20 and current_stoch_d < 20:
            conditions.append("Strong selling pressure")
        else:
            conditions.append("Balanced market")
        
        return ", ".join(conditions)

    def _explain_trade(self, action: str, rsi: float, stoch_k: float, adx: float) -> str:
        """Generate detailed trade explanation based on indicators"""
        explanation = []
        
        # Action explanation
        explanation.append(f"Action: {action.upper()} signal generated")
        
        # Trend explanation
        if adx > 40:
            if action == 'buy':
                explanation.append("Strong trend confirmation - ADX above 40")
            else:
                explanation.append("Strong trend reversal signal - ADX above 40")
        elif adx > 25:
            explanation.append("Moderate trend strength - ADX between 25-40")
        else:
            explanation.append("Weak trend strength - ADX below 25")
        
        # Momentum explanation
        if action == 'buy':
            if rsi < 30:
                explanation.append("Oversold conditions confirmed by RSI")
            elif rsi < 50:
                explanation.append("Neutral to bullish momentum")
            else:
                explanation.append("Bullish momentum confirmed by RSI")
        else:
            if rsi > 70:
                explanation.append("Overbought conditions confirmed by RSI")
            elif rsi > 50:
                explanation.append("Neutral to bearish momentum")
            else:
                explanation.append("Bearish momentum confirmed by RSI")
        
        # Stochastic explanation
        if action == 'buy':
            if stoch_k < 20:
                explanation.append("Strong buy signal from Stochastic Oscillator")
            elif stoch_k < 50:
                explanation.append("Moderate buy signal from Stochastic Oscillator")
        else:
            if stoch_k > 80:
                explanation.append("Strong sell signal from Stochastic Oscillator")
            elif stoch_k > 50:
                explanation.append("Moderate sell signal from Stochastic Oscillator")
        
        # Confidence level
        confidence = round(self.data['confidence'].iloc[-1], 1)
        explanation.append(f"Confidence Level: {confidence}%")
        
        return ". ".join(explanation) + "."

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