import pytest
from datetime import datetime, timezone
from app.services.education_service import EducationService
from app.services.signal_generation_service import SignalGenerationService
from app.services.usage_tracking_service import UsageTrackingService
from app.models.models import User, Subscription

@pytest.fixture
def user():
    return User(
        id=1,
        email="test@example.com",
        subscription=Subscription(
            tier='premium',
            is_active=True,
            start_date=datetime.now(timezone.utc)
        )
    )

@pytest.mark.asyncio
async def test_educational_content_access(user):
    db = SessionLocal()
    education_service = EducationService(db)
    content = await education_service.get_educational_content(user)
    
    assert len(content) > 0
    assert all(isinstance(item['title'], str) for item in content)
    assert all(isinstance(item['level'], int) for item in content)

@pytest.mark.asyncio
async def test_signal_generation(user):
    db = SessionLocal()
    signal_service = SignalGenerationService(db)
    signals = await signal_service.get_signals(user)
    
    assert len(signals) > 0
    assert all(isinstance(signal['symbol'], str) for signal in signals)
    assert all(isinstance(signal['confidence'], float) for signal in signals)

@pytest.mark.asyncio
async def test_usage_tracking(user):
    db = SessionLocal()
    usage_service = UsageTrackingService(db)
    
    # Test tracking for different features
    features = ['signal_requests', 'ai_consultations', 'educational_access']
    results = []
    
    for feature in features:
        result = await usage_service.track_usage(user, feature)
        results.append(result)
    
    assert all(results)  # All should be True for premium user
