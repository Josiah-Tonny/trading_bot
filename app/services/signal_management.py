from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.user import User, Subscription, SubscriptionTier
from app.signals.types import SignalResult, TradingSignal
from app.signals.engine import SignalEngine
from app.services.subscription_pricing import SubscriptionPricing
from app.signals.engine import SignalEngine
import random

class SignalManagementService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.signal_engine = SignalEngine()
        
    async def generate_signals(
        self, user_id: int, symbol: str, timeframe: str
    ) -> SignalResult:
        """Generate signals based on user's subscription tier"""
        # Get user's subscription
        result = await self.session.execute(
            select(User)
            .filter(User.id == user_id)
            .options(joinedload(User.subscription))
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.subscription:
            raise ValueError("User has no active subscription")
            
        subscription = user.subscription
        
        # Validate timeframe access
        if timeframe not in subscription.tier.signal_limits['timeframes']:
            raise ValueError(f"Timeframe {timeframe} not available in {subscription.tier.value} tier")
            
        # Create signal engine with subscription tier
        engine = SignalEngine(
            symbol=symbol, 
            timeframe=timeframe,
            subscription_tier=subscription.tier
        )
        
        # Generate signal with tier-specific features
        signal_result = engine.generate_signal_with_permissions(
            capital=float(subscription.capital),
            risk_profile=subscription.risk_profile
        )
        
        # Update usage tracking
        await self._update_usage_tracking(subscription)
        
        return signal_result

    async def can_change_signal(
        self, user_id: int, new_symbol: str
    ) -> Dict[str, Any]:
        """Check if user can change their signal based on subscription"""
        result = await self.session.execute(
            select(Subscription)
            .filter(Subscription.user_id == user_id)
            .filter(Subscription.end_date > datetime.now(timezone.utc))
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return {
                "allowed": False,
                "reason": "No active subscription",
                "fee": None
            }
        
        # Get signal change fee and limits for tier
        fee = subscription.tier.signal_change_fee
        limits = subscription.tier.signal_limits
        
        # Check custom signal limit
        if subscription.signal_changes_made >= limits['custom_signals']:
            return {
                "allowed": False,
                "reason": "Maximum signal changes reached for subscription tier",
                "fee": None
            }
        
        return {
            "allowed": True,
            "reason": "Signal change allowed",
            "fee": fee if fee > 0 else None
        }
    
    async def change_signal(
        self, user_id: int, new_symbol: str, timeframe: str, payment_confirmed: bool = False
    ) -> Dict[str, Any]:
        """Change user's signal after confirming payment if required"""
        check_result = await self.can_change_signal(user_id, new_symbol)
        
        if not check_result["allowed"]:
            return {"success": False, "message": check_result["reason"]}
            
        if check_result.get("fee") and not payment_confirmed:
            return {
                "success": False,
                "message": "Payment required",
                "fee": check_result["fee"]
            }
            
        try:
            result = await self.session.execute(
                select(Subscription)
                .filter(Subscription.user_id == user_id)
                .filter(Subscription.end_date > datetime.now(timezone.utc))
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return {"success": False, "message": "No active subscription"}
            
            # Validate timeframe access
            if timeframe not in subscription.tier.signal_limits['timeframes']:
                return {
                    "success": False,
                    "message": f"Timeframe {timeframe} not available in {subscription.tier.value} tier"
                }
            
            # Generate new signal with tier features
            signal_result = await self.generate_signals(user_id, new_symbol, timeframe)
            
            # Update subscription tracking
            subscription.signal_changes_made += 1
            subscription.last_signal_change = datetime.now(timezone.utc)
            await self.session.commit()
            
            return {
                "success": True,
                "message": "Signal changed successfully",
                "signal": signal_result
            }
            
        except Exception as e:
            await self.session.rollback()
            return {"success": False, "message": str(e)}
            
    async def get_random_signals(
        self, user_id: int, count: int = 2
    ) -> List[SignalResult]:
        """Generate random signals for free tier users"""
        common_symbols = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "ETHUSD"]
        signals: List[SignalResult] = []
        
        # Get user's subscription tier
        result = await self.session.execute(
            select(User)
            .filter(User.id == user_id)
            .options(joinedload(User.subscription))
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.subscription:
            raise ValueError("User has no active subscription")
        
        for _ in range(min(count, user.subscription.tier.signal_limits['random_signals'])):
            symbol = random.choice(common_symbols)
            signal_result = await self.generate_signals(
                user_id=user_id,
                symbol=symbol,
                timeframe="1h"  # Default timeframe for random signals
            )
            signals.append(signal_result)
            
        return signals
