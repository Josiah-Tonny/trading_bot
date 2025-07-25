from typing import TypedDict, Dict, List, Union, Optional
from decimal import Decimal
from datetime import datetime

class SignalIndicators(TypedDict):
    """Technical indicators used in signal generation"""
    rsi: float
    adx: float
    stoch_k: float
    stoch_d: float
    atr: float
    std_dev: float
    macd: float
    signal_line: float
    histogram: float

class TradingSignal(TypedDict):
    """Trading signal with full type information"""
    symbol: str
    timeframe: str
    action: str  # 'buy', 'sell', or 'hold'
    entry: float
    tp: List[float]  # Multiple take profit targets
    sl: float
    confidence: float
    timestamp: datetime
    indicators: SignalIndicators
    trade_info: Dict[str, str]  # Additional trade metadata

class SignalPermissions(TypedDict):
    """User's signal permissions based on subscription"""
    custom_signals_remaining: Union[int, float]
    allowed_timeframes: List[str]
    requests_remaining: int
    advanced_indicators: bool
    portfolio_optimization: bool
    risk_analysis: bool

class SignalResult(TypedDict):
    """Complete signal generation result"""
    signal: TradingSignal
    permissions: SignalPermissions
    advanced_analysis: Optional[Dict[str, Any]]  # Available for pro/premium tiers
