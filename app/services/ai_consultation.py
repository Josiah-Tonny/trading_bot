import os
import json
from datetime import datetime, timedelta, timezone
import httpx
from typing import Optional, Dict, Any
import os
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import User, Subscription

class AIConsultationService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv('AIMLAPI_AI_API_KEY')
        self.base_url = 'https://api.aimlapi.com/v1'
        self.requests_per_tier = {
            'free': 10,     # 10 requests/hour as per free tier
            'pro': 100,     # Increased limits for paid tiers
            'premium': 500   # Maximum limit for premium users
        }
        
        # AI consultation features by tier
        self.tier_features = {
            'free': {
                'sentiment_analysis': True,
                'basic_signals': True,
                'risk_analysis': False,
                'portfolio_optimization': False
            },
            'pro': {
                'sentiment_analysis': True,
                'advanced_signals': True,
                'risk_analysis': True,
                'portfolio_optimization': False
            },
            'premium': {
                'sentiment_analysis': True,
                'advanced_signals': True,
                'risk_analysis': True,
                'portfolio_optimization': True,
                'custom_strategy': True
            }
        }

    async def _make_api_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make an API request to AIMLAPI"""
        if not self.api_key:
            return {'error': 'AI API key not configured'}

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f'{self.base_url}/{endpoint}',
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"API request failed: {e}")
                return {'error': str(e)}
            except Exception as e:
                print(f"Unexpected error in AI API request: {e}")
                return {'error': 'Internal service error'}

    async def _check_rate_limit(self, subscription: Subscription) -> bool:
        """Check if the user has exceeded their hourly request limit"""
        if not subscription.ai_consultation_enabled:
            return False
            
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        
        # Update request count
        if not subscription.last_ai_request or subscription.last_ai_request < hour_ago:
            subscription.ai_requests_count = 0  # Reset counter for new hour
        if not subscription.last_ai_request or subscription.last_ai_request < hour_ago:
            subscription.ai_requests_count = 1
        else:
            subscription.ai_requests_count += 1
            
        subscription.last_ai_request = now
        self.db.commit()
        
        return subscription.ai_requests_count <= self.requests_per_tier.get(subscription.tier, 0)

    def get_request_limit(self, subscription: Subscription) -> int:
        """Get the hourly request limit based on subscription tier"""
        return self.requests_per_tier.get(subscription.tier, 0)

    async def get_trading_advice(self, 
                               user: User, 
                               subscription: Subscription,
                               market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered trading advice based on market data"""
        if not subscription.ai_consultation_enabled:
            return {'error': 'AI consultation not enabled for this subscription'}

        # Check request limits
        request_limit = self.get_request_limit(subscription)
        if request_limit <= 0:
            return {'error': 'No AI consultation requests available'}

        # Prepare data for AI analysis
        analysis_request: Dict[str, Any] = {
            'market_data': market_data,
            'user_risk_tolerance': user.risk_tolerance,
            'analysis_type': 'trading_advice'
        }

        return await self._make_api_request('analyze/trading', analysis_request)

    async def get_portfolio_optimization(self, 
                                      user: User,
                                      subscription: Subscription, 
                                      portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered portfolio optimization recommendations"""
        if not await self._check_rate_limit(subscription):
            return {'error': 'Rate limit exceeded', 'remaining_time': '1 hour'}

        if subscription.tier != 'premium':
            return {'error': 'Portfolio optimization is a premium feature'}

        if not subscription.ai_consultation_enabled:
            return {'error': 'AI consultation not enabled'}

        optimization_request: Dict[str, Any] = {
            'portfolio': portfolio,
            'risk_tolerance': user.risk_tolerance,
            'analysis_type': 'portfolio_optimization'
        }

        return await self._make_api_request('analyze/portfolio', optimization_request)

    async def get_signal_quality_score(self,
                                     user: User,
                                     subscription: Subscription,
                                     signal: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered signal quality score"""
        if not await self._check_rate_limit(subscription):
            return {'error': 'Rate limit exceeded', 'remaining_time': '1 hour'}

        if not subscription.ai_consultation_enabled:
            return {'error': 'AI consultation not enabled'}

        score_request: Dict[str, Any] = {
            'signal': signal,
            'market_context': True,
            'analysis_type': 'signal_quality'
        }

        return await self._make_api_request('analyze/signal', score_request)
