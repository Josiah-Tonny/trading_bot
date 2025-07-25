from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import DatabaseModel, DatabaseOperations
import enum

class UsageMetricType(str, enum.Enum):
    """Types of usage metrics to track"""
    SIGNAL_GENERATION = "signal_generation"
    API_REQUESTS = "api_requests"
    CONTENT_ACCESS = "content_access"
    CUSTOM_SIGNALS = "custom_signals"
    EDUCATIONAL_ACCESS = "educational_access"

class UsageMetric(DatabaseModel):
    """Model for tracking usage metrics"""
    __tablename__ = 'usage_metrics'
    
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    metric_type: Mapped[UsageMetricType] = mapped_column(Enum(UsageMetricType))
    count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    daily_limit: Mapped[Optional[int]] = mapped_column(Integer)
    hourly_limit: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="usage_metrics")

class UsageLimit(DatabaseModel):
    """Model for user-specific usage limits"""
    __tablename__ = 'usage_limits'
    
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    metric_type: Mapped[UsageMetricType] = mapped_column(Enum(UsageMetricType))
    daily_limit: Mapped[int] = mapped_column(Integer)
    hourly_limit: Mapped[int] = mapped_column(Integer)
    current_usage: Mapped[int] = mapped_column(Integer, default=0)
    last_reset: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="usage_limits")

class UsageMetricOperations(DatabaseOperations[UsageMetric]):
    """Database operations for usage metrics"""
    
    @property
    def model_type(self) -> type[UsageMetric]:
        return UsageMetric
    
    async def get_user_metrics(self, user_id: int) -> List[UsageMetric]:
        """Get all metrics for a user"""
        stmt = self.select().where(UsageMetric.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars())
    
    async def increment_metric(self, user_id: int, metric_type: UsageMetricType) -> UsageMetric:
        """Increment usage metric count"""
        stmt = self.select().where(
            UsageMetric.user_id == user_id,
            UsageMetric.metric_type == metric_type
        )
        metric = await self.session.scalar(stmt)
        
        if not metric:
            metric = await self.create(
                user_id=user_id,
                metric_type=metric_type,
                count=1
            )
        else:
            metric.count += 1
            metric.last_used = datetime.now(timezone.utc)
            await self.session.flush()
        
        return metric

class UsageLimitOperations(DatabaseOperations[UsageLimit]):
    """Database operations for usage limits"""
    
    @property
    def model_type(self) -> type[UsageLimit]:
        return UsageLimit
    
    async def check_limit(self, user_id: int, metric_type: UsageMetricType) -> bool:
        """Check if usage is within limits"""
        stmt = self.select().where(
            UsageLimit.user_id == user_id,
            UsageLimit.metric_type == metric_type
        )
        limit = await self.session.scalar(stmt)
        
        if not limit:
            return True  # No limit set
            
        now = datetime.now(timezone.utc)
        
        # Reset daily usage if needed
        if (now - limit.last_reset).days >= 1:
            limit.current_usage = 0
            limit.last_reset = now
            await self.session.flush()
        
        return limit.current_usage < limit.daily_limit
    
    async def increment_usage(self, user_id: int, metric_type: UsageMetricType) -> bool:
        """Increment usage count and check limits"""
        stmt = self.select().where(
            UsageLimit.user_id == user_id,
            UsageLimit.metric_type == metric_type
        )
        limit = await self.session.scalar(stmt)
        
        if not limit:
            return True  # No limit set
            
        if await self.check_limit(user_id, metric_type):
            limit.current_usage += 1
            await self.session.flush()
            return True
            
        return False  # Limit exceeded
        
    async def update_limits(self, user_id: int, metric_type: UsageMetricType, 
                          daily_limit: int, hourly_limit: int) -> UsageLimit:
        """Update usage limits for a metric"""
        stmt = self.select().where(
            UsageLimit.user_id == user_id,
            UsageLimit.metric_type == metric_type
        )
        limit = await self.session.scalar(stmt)
        
        if limit:
            limit.daily_limit = daily_limit
            limit.hourly_limit = hourly_limit
            await self.session.flush()
        else:
            limit = await self.create(
                user_id=user_id,
                metric_type=metric_type,
                daily_limit=daily_limit,
                hourly_limit=hourly_limit
            )
            
        return limit
