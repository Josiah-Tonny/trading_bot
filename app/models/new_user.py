from typing import Optional, Dict, Any, TypedDict
from datetime import datetime, timezone
import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, Float, ForeignKey, Enum, BigInteger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from app.models.base import DatabaseModel, DatabaseOperations

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
        """Get user by telegram ID"""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.scalar(stmt)
        return result

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.session.scalar(stmt)
        return result

    async def create(self, **data: Any) -> User:
        """Create new user"""
        user = User(**data)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User, **data: Any) -> User:
        """Update user data"""
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        """Delete user"""
        self.session.delete(user)
        await self.session.flush()

class SubscriptionOperations(DatabaseOperations[Subscription]):
    """Subscription database operations implementation"""
    
    async def get_by_id(self, id: int) -> Optional[Subscription]:
        """Get subscription by ID"""
        stmt = select(Subscription).where(Subscription.id == id)
        result = await self.session.scalar(stmt)
        return result

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

    async def update(self, subscription: Subscription, **data: Any) -> Subscription:
        """Update subscription data"""
        for key, value in data.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)
        await self.session.flush()
        return subscription

    async def delete(self, subscription: Subscription) -> None:
        """Delete subscription"""
        self.session.delete(subscription)
        await self.session.flush()
