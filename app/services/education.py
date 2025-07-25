from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional, List

from app.models.education import (
    EducationalContent, ContentView, UserProgress,
    EducationalContentOperations, ContentViewOperations, UserProgressOperations
)
from app.models.usage import (
    UsageMetric, UsageLimit, UsageMetricOperations, UsageLimitOperations
)
from app.models.user import User, SubscriptionTier

class EducationService:
    """Service layer for handling educational content and user progress"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.content_ops = EducationalContentOperations(session)
        self.view_ops = ContentViewOperations(session)
        self.progress_ops = UserProgressOperations(session)
    
    async def get_available_content(self, user_id: int, subscription_tier: SubscriptionTier) -> List[EducationalContent]:
        """Get content available for user's subscription tier"""
        content = await self.content_ops.get_for_tier(subscription_tier.value)
        views = await self.view_ops.get_user_views(user_id)
        
        # Enrich content with user's progress
        view_map = {view.content_id: view for view in views}
        for item in content:
            if item.id in view_map:
                setattr(item, 'user_progress', view_map[item.id].progress_percent)
                setattr(item, 'completed', view_map[item.id].completed)
            else:
                setattr(item, 'user_progress', 0)
                setattr(item, 'completed', False)
        
        return content
    
    async def record_content_view(self, user_id: int, content_id: int, progress: int) -> None:
        """Record or update a user's progress on content"""
        # Get existing view
        stmt = select(ContentView).where(
            ContentView.user_id == user_id,
            ContentView.content_id == content_id
        )
        view = await self.session.scalar(stmt)
        
        if view:
            # Update existing view
            await self.view_ops.update_progress(view.id, progress)
        else:
            # Create new view
            await self.view_ops.create(
                user_id=user_id,
                content_id=content_id,
                progress_percent=progress,
                completed=progress >= 100
            )
        
        # Update user progress if completed
        if progress >= 100:
            await self.update_user_progress(user_id)
    
    async def update_user_progress(self, user_id: int) -> UserProgress:
        """Update user's overall learning progress"""
        # Get user's content views
        views = await self.view_ops.get_user_views(user_id)
        total_content = len(views)
        completed_content = len([v for v in views if v.completed])
        
        # Get or create user progress
        progress = await self.progress_ops.get_user_progress(user_id)
        if not progress:
            progress = await self.progress_ops.create(
                user_id=user_id,
                total_content_viewed=total_content,
                total_content_completed=completed_content
            )
        else:
            progress = await self.progress_ops.update(
                progress,
                total_content_viewed=total_content,
                total_content_completed=completed_content
            )
        
        # Update level based on completion percentage
        completion_rate = completed_content / total_content if total_content > 0 else 0
        if completion_rate >= 0.8:
            progress.points_earned += 100  # Bonus points for high completion
        
        await self.session.flush()
        return progress

class UsageTrackingService:
    """Service layer for tracking user usage and enforcing limits"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.metric_ops = UsageMetricOperations(session)
        self.limit_ops = UsageLimitOperations(session)
    
    async def track_usage(self, user_id: int, metric_type: str) -> bool:
        """Track usage of a feature and check if limit is exceeded"""
        # First check if we can use this feature
        if not await self.limit_ops.check_limit(user_id, metric_type):
            return False
            
        # Record the usage
        await self.metric_ops.increment_metric(user_id, metric_type)
        await self.limit_ops.increment_usage(user_id, metric_type)
        
        return True
    
    async def get_usage_stats(self, user_id: int) -> dict:
        """Get usage statistics for a user"""
        metrics = await self.metric_ops.get_user_metrics(user_id)
        return {
            metric.metric_type: {
                'count': metric.count,
                'last_used': metric.last_used.isoformat() if metric.last_used else None
            }
            for metric in metrics
        }
    
    async def reset_daily_limits(self) -> None:
        """Reset daily usage limits - should be called by a scheduled task"""
        stmt = select(UsageLimit)
        result = await self.session.execute(stmt)
        limits = result.scalars().all()
        
        for limit in limits:
            limit.current_usage = 0
            limit.last_reset = datetime.now(timezone.utc)
        
        await self.session.flush()
