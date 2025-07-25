from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.education import ContentLevel, ContentType, EducationalContent
from app.models.user import User, SubscriptionTier
from app.services.education import EducationService, UsageTrackingService
from app.models.base import get_session
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["education"])

@router.get("/education/content")
async def get_education_content(
    level: Optional[ContentLevel] = None,
    content_type: Optional[ContentType] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> List[dict]:
    """Get educational content available to user"""
    education_service = EducationService(session)
    usage_service = UsageTrackingService(session)
    
    # Track content access
    can_access = await usage_service.track_usage(
        current_user.id, 
        "CONTENT_ACCESS"
    )
    if not can_access:
        raise HTTPException(
            status_code=429,
            detail="Daily content access limit reached"
        )
    
    # Get available content
    content = await education_service.get_available_content(
        current_user.id,
        current_user.subscription.tier if current_user.subscription else SubscriptionTier.FREE
    )
    
    # Filter by level and type if specified
    if level:
        content = [c for c in content if c.level == level]
    if content_type:
        content = [c for c in content if c.content_type == content_type]
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "content_type": c.content_type,
            "level": c.level,
            "duration_minutes": c.duration_minutes,
            "progress": getattr(c, "user_progress", 0),
            "completed": getattr(c, "completed", False),
            "content_url": c.content_url
        }
        for c in content
    ]

@router.post("/education/content/{content_id}/progress")
async def update_content_progress(
    content_id: int,
    progress: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Update user's progress on educational content"""
    if not 0 <= progress <= 100:
        raise HTTPException(
            status_code=400,
            detail="Progress must be between 0 and 100"
        )
    
    education_service = EducationService(session)
    await education_service.record_content_view(
        current_user.id,
        content_id,
        progress
    )
    
    return {"status": "success", "progress": progress}

@router.get("/education/progress")
async def get_learning_progress(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get user's learning progress"""
    education_service = EducationService(session)
    progress = await education_service.progress_ops.get_user_progress(current_user.id)
    
    if not progress:
        return {
            "level": "beginner",
            "total_content": 0,
            "completed_content": 0,
            "points": 0
        }
    
    return {
        "level": progress.current_level,
        "total_content": progress.total_content_viewed,
        "completed_content": progress.total_content_completed,
        "points": progress.points_earned
    }

@router.get("/usage/stats")
async def get_usage_statistics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get user's feature usage statistics"""
    usage_service = UsageTrackingService(session)
    stats = await usage_service.get_usage_stats(current_user.id)
    
    return {
        "usage_stats": stats,
        "subscription_tier": current_user.subscription.tier.value if current_user.subscription else "free",
        "education_level": current_user.education_level or "beginner",
        "completion_rate": current_user.completion_percentage
    }
