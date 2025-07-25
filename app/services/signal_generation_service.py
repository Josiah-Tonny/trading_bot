from typing import Dict, List, Optional, TypedDict, Any
from datetime import datetime, timezone
import httpx
import os
from sqlalchemy.orm import Session
from app.models.models import User, Subscription

class MarketSignal(TypedDict):
    symbol: str
    direction: str
    confidence: float
    indicators: Dict[str, Any]
    timestamp: datetime

class SignalGenerationService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv('AIMLAPI_AI_API_KEY')
        self.base_url = 'https://api.aimlapi.com/v1/signals'

    async def _generate_signals(self, 
                              symbols: List[str], 
                              timeframes: List[str],
                              advanced: bool = False) -> List[MarketSignal]:
        """Generate trading signals using AI API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate",
                json={
                    "symbols": symbols,
                    "timeframes": timeframes,
                    "advanced": advanced
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()

    async def get_signals(self, user: User) -> List[MarketSignal]:
        """Get signals based on user's subscription tier"""
        if not user.subscription:
            return []

        # Get user's allowed symbols and timeframes
        symbols = ['EURUSD', 'GBPUSD']  # Default basic pairs
        timeframes = ['1H', '4H']  # Default timeframes

        advanced_analysis = user.subscription.tier in ['pro', 'premium']
        
        signals = await self._generate_signals(
            symbols=symbols,
            timeframes=timeframes,
            advanced=advanced_analysis
        )

        # Filter signals based on subscription level
        max_signals = {
            'free': 2,
            'pro': 5,
            'premium': float('inf')
        }.get(user.subscription.tier, 2)

        return signals[:max_signals] if max_signals != float('inf') else signals

    async def get_signal_analytics(self, user: User, signal: MarketSignal) -> Dict[str, Any]:
        """Get detailed signal analytics (Premium feature)"""
        if not user.subscription or user.subscription.tier != 'premium':
            return {"error": "Premium subscription required"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/analytics",
                json=signal,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()

    async def validate_signal(self, user: User, signal: MarketSignal) -> Dict[str, Any]:
        """Validate custom signals (Pro/Premium feature)"""
        if not user.subscription or user.subscription.tier == 'free':
            return {"error": "Pro or Premium subscription required"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/validate",
                json=signal,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
