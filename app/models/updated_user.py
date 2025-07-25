"""Update the User model type hints in app.models.base"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Boolean

from app.models.base import DatabaseModel
from app.models.education import ContentView, UserProgress
from app.models.usage import UsageMetric, UsageLimit

class User(DatabaseModel):
    """User model with full type hints and relationships"""
    __tablename__ = 'users'
    
    # Basic user information
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Educational progress and content tracking
    content_views: Mapped[List[ContentView]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    learning_progress: Mapped[Optional[UserProgress]] = relationship(
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    
    # Usage tracking
    usage_metrics: Mapped[List[UsageMetric]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    usage_limits: Mapped[List[UsageLimit]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    # Existing relationships
    subscription: Mapped[Optional['Subscription']] = relationship(
        'Subscription',
        back_populates='user',
        uselist=False,
        cascade="all, delete-orphan"
    )

    def can_access_feature(self, feature_name: str) -> bool:
        """Check if user can access a feature based on subscription"""
        if not self.subscription or not self.subscription.is_active:
            return False
        return feature_name in self.subscription.features

    def has_reached_limit(self, metric_type: str) -> bool:
        """Check if user has reached usage limit for a metric"""
        for limit in self.usage_limits:
            if limit.metric_type == metric_type:
                return limit.current_usage >= limit.daily_limit
        return False

    @property
    def education_level(self) -> Optional[str]:
        """Get user's current education level"""
        if self.learning_progress:
            return self.learning_progress.current_level
        return None

    @property
    def completion_percentage(self) -> float:
        """Calculate overall content completion percentage"""
        if not self.content_views:
            return 0.0
        
        completed = sum(1 for view in self.content_views if view.completed)
        return (completed / len(self.content_views)) * 100
