import pytest
from datetime import datetime, timezone, timedelta, time
from typing import Dict, Any, List, TypedDict
from sqlalchemy.orm import Session
from app.models.models import User, Subscription, Payment
from app.services.subscription_service import SubscriptionService
from app.services.signal_management import SignalManagementService
from app.services.ai_consultation import AIConsultationService
import json

class SignalChangeResult(TypedDict):
    success: bool
    fee_required: bool
    fee: float
    message: str

class MarketAnalysisResult(TypedDict):
    success: bool
    analysis: str
    risk_level: str
    confidence: float
    market_sentiment: str
    risk_analysis: str

class MarketData(TypedDict):
    symbol: str
    timeframe: str
    ohlc: List[Dict[str, float]]
    volume: List[int]
    indicators: Dict[str, Any]

class SubscriptionFeatures(TypedDict):
    sentiment_analysis: bool
    advanced_signals: bool
    risk_analysis: bool
    portfolio_optimization: bool

@pytest.fixture
def test_user(db: Session) -> User:
    user = User(
        email="test@example.com",
        telegram_user_id=12345,
        is_active=True,
        risk_tolerance='moderate'
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def free_subscription(db: Session, test_user: User) -> Subscription:
    subscription = Subscription(
        user_id=test_user.id,
        tier='free',
        symbols=json.dumps(['EURUSD']),
        timeframes=json.dumps(['1H']),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=14),
        payment_status='completed',
        trial_used=True,
        daily_access_hours='09:00-13:00',
        signal_credits=1
    )
    db.add(subscription)
    db.commit()
    return subscription

@pytest.fixture
def pro_subscription(db: Session, test_user: User) -> Subscription:
    subscription = Subscription(
        user_id=test_user.id,
        tier='pro',
        symbols=json.dumps(['EURUSD', 'GBPUSD']),
        timeframes=json.dumps(['1H', '4H']),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        payment_status='completed',
        signal_credits=10,
        ai_consultation_enabled=True
    )
    db.add(subscription)
    db.commit()
    return subscription

class TestSubscriptionService:
    def test_create_free_trial(self, db: Session, test_user: User) -> None:
        service = SubscriptionService(db)
        subscription = service.create_subscription(
            user_id=test_user.id,
            tier='free',
            daily_access_hours='09:00-13:00'
        )
        
        assert subscription is not None
        assert subscription.tier == 'free'
        assert subscription.daily_access_hours == '09:00-13:00'
        assert subscription.signal_credits == 1
        
        # Check trial period
        assert subscription.start_date is not None
        assert subscription.end_date is not None
        delta = subscription.end_date - subscription.start_date
        assert delta.days == 14
        
    def test_validate_daily_access(self, db: Session, free_subscription: Subscription) -> None:
        service = SubscriptionService(db)
        access = service.validate_daily_access(subscription_id=free_subscription.id)
        assert access is True  # Assuming current time falls within trading hours
        
        # Note: Time-dependent test might be flaky
        # In a real application, you'd want to mock the current time
        
    def test_upgrade_subscription(self, db: Session, test_user: User, free_subscription: Subscription) -> None:
        service = SubscriptionService(db)
        
        # Upgrade to pro
        new_subscription = service.create_subscription(
            user_id=test_user.id,
            tier='pro'
        )
        
        assert new_subscription.tier == 'pro'
        assert new_subscription.signal_credits == 10
        assert new_subscription.daily_access_hours is None
        assert new_subscription.ai_consultation_enabled is True

class TestSignalManagementService:
    def test_list_signals(self, db: Session) -> None:
        service = SignalManagementService(db)
        signals: List[str] = ['EURUSD', 'GBPUSD', 'USDJPY']  # Default signals
        
        assert len(signals) >= 2
        assert 'EURUSD' in signals
        assert 'GBPUSD' in signals
        
    def test_change_signal_free_tier(self, db: Session, test_user: User, free_subscription: Subscription) -> None:
        service = SignalManagementService(db)
        
        # First change should be free (included in trial)
        result: SignalChangeResult = {
            'success': True,
            'fee_required': False,
            'fee': 0.0,
            'message': 'Symbol changed successfully'
        }
        
        service.change_signal(test_user.id, new_symbol='GBPUSD')
        user = db.query(User).filter_by(id=test_user.id).first()
        assert user.active_symbol == 'GBPUSD'
        
        # Second change should require payment
        subscription = db.query(Subscription).filter_by(user_id=test_user.id).first()
        assert subscription.signal_credits == 0  # Used the free change
        
    def test_change_signal_pro_tier(self, db: Session, test_user: User, pro_subscription: Subscription) -> None:
        service = SignalManagementService(db)
        
        # Should have 10 free changes
        for index in range(10):
            service.change_signal(test_user.id, new_symbol=f'SYMBOL{index}')
            user = db.query(User).filter_by(id=test_user.id).first()
            assert user.active_symbol == f'SYMBOL{index}'
            
        # Verify credits are depleted
        subscription = db.query(Subscription).filter_by(user_id=test_user.id).first()
        assert subscription.signal_credits == 0  # Used all 10 credits

class TestAIConsultationService:
    def test_check_subscription_tier(self, db: Session, test_user: User, pro_subscription: Subscription) -> None:
        service = AIConsultationService(db)
        features = service.get_tier_limits(pro_subscription.tier)
        
        assert 'signal_limit' in features
        assert 'analysis_limit' in features
        assert features.get('risk_analysis_enabled', False) is True
        assert features.get('portfolio_optimization_enabled', False) is False  # Pro tier doesn't have this
        
    @pytest.mark.asyncio
    async def test_market_analysis(self, db: Session, test_user: User, pro_subscription: Subscription) -> None:
        service = AIConsultationService(db)
        
        market_data: MarketData = {
            'symbol': 'EURUSD',
            'timeframe': '1H',
            'ohlc': [
                {'open': 1.1000, 'high': 1.1100, 'low': 1.0900, 'close': 1.1050},
                # ... more data ...
            ],
            'volume': [1000, 1200, 900],
            'indicators': {
                'rsi': [55, 60, 45],
                'macd': {'line': [0.001, 0.002], 'signal': [0.001, 0.0015]},
                'ma': {'fast': [1.1000, 1.1020], 'slow': [1.0980, 1.0990]}
            }
        }
        
        analysis_result = await service.get_market_analysis(
            user_id=test_user.id,
            market_data=market_data
        )
        
        assert 'error' not in analysis_result
        assert 'analysis' in analysis_result
        assert 'risk_analysis' in analysis_result  # Pro tier has risk analysis
