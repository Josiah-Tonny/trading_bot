from typing import Dict, List, Optional, TypedDict
from datetime import datetime, timezone
import httpx
import os
from sqlalchemy.orm import Session
from app.models.models import User, Subscription

class EducationalContent(TypedDict):
    title: str
    content: str
    level: int
    category: str
    created_at: datetime

class EducationService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv('AIMLAPI_AI_API_KEY')
        self.base_url = 'https://api.aimlapi.com/v1/education'

    async def _fetch_content(self, category: str, level: int) -> List[EducationalContent]:
        """Fetch educational content from AI API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/content",
                params={
                    "category": category,
                    "level": level
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()

    async def get_educational_content(self, user: User) -> List[EducationalContent]:
        """Get educational content based on user's subscription level"""
        if not user.subscription:
            return []

        level_mapping = {
            'free': 1,
            'pro': 2,
            'premium': 3
        }

        content_level = level_mapping.get(user.subscription.tier, 1)
        
        categories = ['trading_basics', 'technical_analysis', 'risk_management']
        if content_level >= 2:
            categories.extend(['advanced_strategies', 'market_psychology'])
        if content_level >= 3:
            categories.extend(['algorithmic_trading', 'portfolio_management'])

        all_content = []
        for category in categories:
            content = await self._fetch_content(category, content_level)
            all_content.extend(content)

        return all_content

    async def track_content_access(self, user: User, content_id: str) -> bool:
        """Track user's content access and update usage metrics"""
        if not user.subscription:
            return False

        # Update access tracking
        now = datetime.now(timezone.utc)
        # Implement access tracking logic here
        return True
