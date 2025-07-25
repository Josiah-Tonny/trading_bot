from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import DatabaseModel, DatabaseOperations
import enum

class ContentLevel(str, enum.Enum):
    """Content access levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class ContentType(str, enum.Enum):
    """Types of educational content"""
    ARTICLE = "article"
    VIDEO = "video"
    WEBINAR = "webinar"
    COURSE = "course"
    QUIZ = "quiz"

class EducationalContent(DatabaseModel):
    """Model for educational content"""
    __tablename__ = 'educational_content'
    
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType))
    level: Mapped[ContentLevel] = mapped_column(Enum(ContentLevel))
    content_url: Mapped[str] = mapped_column(String(500))
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    requires_subscription: Mapped[bool] = mapped_column(Boolean, default=True)
    min_subscription_tier: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    views: Mapped[List["ContentView"]] = relationship(back_populates="content", cascade="all, delete-orphan")

class ContentView(DatabaseModel):
    """Track user content views and progress"""
    __tablename__ = 'content_views'
    
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    content_id: Mapped[int] = mapped_column(ForeignKey('educational_content.id'))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    last_viewed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    view_count: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    content: Mapped[EducationalContent] = relationship(back_populates="views")
    user: Mapped["User"] = relationship(back_populates="content_views")

class UserProgress(DatabaseModel):
    """Track overall user learning progress"""
    __tablename__ = 'user_progress'
    
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    current_level: Mapped[ContentLevel] = mapped_column(
        Enum(ContentLevel),
        default=ContentLevel.BEGINNER
    )
    total_content_viewed: Mapped[int] = mapped_column(Integer, default=0)
    total_content_completed: Mapped[int] = mapped_column(Integer, default=0)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="learning_progress")

class EducationalContentOperations(DatabaseOperations[EducationalContent]):
    """Database operations for educational content"""
    
    async def get_by_level(self, level: ContentLevel) -> List[EducationalContent]:
        """Get content by access level"""
        stmt = self.select().where(EducationalContent.level == level)
        result = await self.session.execute(stmt)
        return list(result.scalars())
    
    async def get_by_type(self, content_type: ContentType) -> List[EducationalContent]:
        """Get content by type"""
        stmt = self.select().where(EducationalContent.content_type == content_type)
        result = await self.session.execute(stmt)
        return list(result.scalars())
    
    async def get_for_tier(self, subscription_tier: str) -> List[EducationalContent]:
        """Get content available for subscription tier"""
        stmt = self.select().where(EducationalContent.min_subscription_tier <= subscription_tier)
        result = await self.session.execute(stmt)
        return list(result.scalars())

class ContentViewOperations(DatabaseOperations[ContentView]):
    """Database operations for content views"""
    
    async def get_user_views(self, user_id: int) -> List[ContentView]:
        """Get all content views for a user"""
        stmt = self.select().where(ContentView.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars())
    
    async def update_progress(self, view_id: int, progress: int) -> ContentView:
        """Update user's progress on content"""
        view = await self.get_by_id(view_id)
        if view:
            view.progress_percent = progress
            view.last_viewed = datetime.now(timezone.utc)
            view.view_count += 1
            if progress >= 100:
                view.completed = True
            await self.session.flush()
        return view

class UserProgressOperations(DatabaseOperations[UserProgress]):
    """Database operations for user progress"""
    
    async def get_user_progress(self, user_id: int) -> Optional[UserProgress]:
        """Get user's learning progress"""
        stmt = self.select().where(UserProgress.user_id == user_id)
        result = await self.session.scalar(stmt)
        return result
    
    async def update_points(self, progress_id: int, points: int) -> UserProgress:
        """Update user's earned points"""
        prog = await self.get_by_id(progress_id)
        if prog:
            prog.points_earned += points
            prog.last_activity = datetime.now(timezone.utc)
            await self.session.flush()
        return prog
