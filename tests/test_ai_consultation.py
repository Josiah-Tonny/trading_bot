import pytest
from datetime import datetime
from app.models.models import User, Subscription
from app.services.ai_consultation import AIConsultationService

@pytest.fixture
def user():
    return User(
        id=1,
        email="test@example.com",
        risk_tolerance="moderate"
    )

@pytest.fixture
def free_subscription():
    return Subscription(
        id=1,
        user_id=1,
        tier='free',
        ai_consultation_enabled=True,
        start_date=datetime.utcnow()
    )

@pytest.fixture
def premium_subscription():
    return Subscription(
        id=2,
        user_id=1,
        tier='premium',
        ai_consultation_enabled=True,
        start_date=datetime.utcnow()
    )

@pytest.fixture
def ai_service():
    return AIConsultationService()

@pytest.mark.asyncio
async def test_trading_advice_free_tier(user, free_subscription, ai_service):
    market_data = {
        'symbol': 'EURUSD',
        'timeframe': '1H',
        'indicators': {'rsi': 65, 'macd': {'value': 0.002}}
    }
    
    result = await ai_service.get_trading_advice(user, free_subscription, market_data)
    assert 'error' not in result
    assert result.get('analysis') is not None

@pytest.mark.asyncio
async def test_portfolio_optimization_premium_only(user, free_subscription, ai_service):
    portfolio = {
        'assets': [
            {'symbol': 'EURUSD', 'allocation': 0.5},
            {'symbol': 'GBPUSD', 'allocation': 0.5}
        ]
    }
    
    result = await ai_service.get_portfolio_optimization(user, free_subscription, portfolio)
    assert 'error' in result
    assert result['error'] == 'Portfolio optimization is a premium feature'

@pytest.mark.asyncio
async def test_signal_quality_score(user, premium_subscription, ai_service):
    signal = {
        'symbol': 'EURUSD',
        'type': 'BUY',
        'entry': 1.1000,
        'stop_loss': 1.0950,
        'take_profit': 1.1100
    }
    
    result = await ai_service.get_signal_quality_score(user, premium_subscription, signal)
    assert 'error' not in result
    assert result.get('score') is not None
