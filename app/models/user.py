from typing import Optional, Dict, Any, TypedDict, Final, Union, List
from datetime import datetime, timezone
import enum
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, Float, ForeignKey, Enum, BigInteger
from sqlalchemy.sql import select

from app.models.base import DatabaseModel, DatabaseOperations

# Signal limit types
class SignalLimits(TypedDict):
    custom_signals: Union[int, float]
    random_signals: Union[int, float]
    requests_per_hour: int
    timeframes: List[str]
    educational_content_access: Optional[List[str]]

# Signal limits and fees constants
TIER_SIGNAL_LIMITS: Final[Dict[str, SignalLimits]] = {
    'free': {
        'custom_signals': 1,
        'random_signals': 2,
        'requests_per_hour': 10,
        'timeframes': ['1h', '4h', '1d'],
        'educational_content_access': ['beginner']
    },
    'pro': {
        'custom_signals': 5,
        'random_signals': 5,
        'requests_per_hour': 100,
        'timeframes': ['15m', '1h', '4h', '1d'],
        'educational_content_access': ['beginner', 'intermediate']
    },
    'premium': {
        'custom_signals': float('inf'),
        'random_signals': float('inf'),
        'requests_per_hour': 500,
        'timeframes': ['5m', '15m', '1h', '4h', '1d'],
        'educational_content_access': ['beginner', 'intermediate', 'advanced', 'expert']
    }
}

SIGNAL_CHANGE_FEES: Final[Dict[str, Decimal]] = {
    'free': Decimal('3.00'),
    'pro': Decimal('1.50'),
    'premium': Decimal('0.00')
}

# Custom type definitions
class FeatureSet(TypedDict, total=False):
    """Features available for each subscription tier"""
    sentiment_analysis: bool
    basic_signals: bool
    advanced_signals: Optional[bool]
    risk_analysis: bool
    portfolio_optimization: bool
    custom_strategy: Optional[bool]

class TelegramData(TypedDict, total=True):
    """Telegram user data structure"""
    telegram_user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]

class SubscriptionTier(str, enum.Enum):
    """Available subscription tiers"""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

    @property
    def features(self) -> FeatureSet:
        """Get features for this tier"""
        return TIER_FEATURES[self]
    
    @property
    def signal_limits(self) -> SignalLimits:
        """Get signal generation limits for this tier"""
        return TIER_SIGNAL_LIMITS[self.value]
    
    @property
    def signal_change_fee(self) -> Decimal:
        """Get signal change fee for this tier"""
        return SIGNAL_CHANGE_FEES[self.value]

TIER_FEATURES: Dict[SubscriptionTier, FeatureSet] = {
    SubscriptionTier.FREE: {
        'sentiment_analysis': True,
        'basic_signals': True,
        'risk_analysis': False,
        'portfolio_optimization': False
    },
    SubscriptionTier.PRO: {
        'sentiment_analysis': True,
        'basic_signals': True,
        'advanced_signals': True,
        'risk_analysis': True,
        'portfolio_optimization': False
    },
    SubscriptionTier.PREMIUM: {
        'sentiment_analysis': True,
        'basic_signals': True,
        'advanced_signals': True,
        'risk_analysis': True,
        'portfolio_optimization': True,
        'custom_strategy': True
    }
}

class User(DatabaseModel):
    """User model with full type hints"""
    __tablename__ = 'users'
    
    # Basic user information
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Trading related fields
    risk_tolerance: Mapped[float] = mapped_column(Float, default=0.5)
    active_symbol: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Telegram integration
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    subscription: Mapped[Optional['Subscription']] = relationship(
        'Subscription',
        back_populates='user',
        uselist=False,
        lazy='joined'
    )

    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        return bool(
            self.subscription and 
            self.subscription.tier == SubscriptionTier.PREMIUM and
            self.subscription.is_active
        )

class Subscription(DatabaseModel):
    """Subscription model with full type hints"""
    __tablename__ = 'subscriptions'
    
    # Foreign key relationship
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    
    # Subscription details
    tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier),
        default=SubscriptionTier.FREE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) 
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Usage tracking
    signal_credits: Mapped[int] = mapped_column(Integer, default=0)
    signal_changes_made: Mapped[int] = mapped_column(Integer, default=0)
    last_signal_change: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_ai_request: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ai_requests_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_consultation_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    user: Mapped[User] = relationship(User, back_populates='subscription')

    @property
    def is_expired(self) -> bool:
        """Check if subscription has expired"""
        if not self.end_date:
            return False
        return datetime.now(timezone.utc) > self.end_date

    @property
    def features(self) -> FeatureSet:
        """Get features for current tier"""
        return TIER_FEATURES[self.tier]

class UserOperations(DatabaseOperations[User]):
    """User database operations implementation"""
    
    async def get_by_id(self, id: int) -> Optional[User]:
        """Get user by ID"""
        stmt = select(User).where(User.id == id)
        result = await self.session.scalar(stmt)
        return result
        
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID with type-safe query"""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.scalar(stmt)
        return result

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.session.scalar(stmt)
        return result

    async def create_telegram_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Create a new user from Telegram data"""
        user = User(
            telegram_id=telegram_id,
            telegram_username=username,
            username=username or f"tg_{telegram_id}",
            email=f"{telegram_id}@telegram.user",
            password_hash="",  # Will be set later
            is_active=True
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create(self, **data: Any) -> User:
        """Create new user"""
        user = User(**data)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, entity: User, **data: Any) -> User:
        """Update user data"""
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        await self.session.flush()
        return entity

    async def delete(self, entity: User) -> None:
        """Delete user"""
        await self.session.delete(entity)
        await self.session.flush()

class SubscriptionOperations(DatabaseOperations[Subscription]):
    """Subscription database operations implementation"""
    
    async def get_by_id(self, id: int) -> Optional[Subscription]:
        """Get subscription by ID"""
        return await self.session.get(Subscription, id)
    
    async def get_by_user_id(self, user_id: int) -> Optional[Subscription]:
        """Get subscription by user ID"""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.session.scalar(stmt)
        return result
    
    async def create(self, **data: Any) -> Subscription:
        """Create new subscription"""
        subscription = Subscription(**data)
        self.session.add(subscription)
        await self.session.flush()
        return subscription
    
    async def update(self, entity: Subscription, **data: Any) -> Subscription:
        """Update subscription data"""
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        await self.session.flush()
        return entity
    
    async def delete(self, entity: Subscription) -> None:
        """Delete subscription"""
        await self.session.delete(entity)
        await self.session.flush()
