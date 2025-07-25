from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import User, Subscription
import json

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.tier_features = {
            'free': {
                'trial_period_days': 14,
                'daily_access_hours': 4,
                'signal_credits': 1,
                'ai_requests_per_hour': 10,
                'allowed_signal_count': 1,
                'education_access_level': 0,
            },
            'pro': {
                'signal_credits': 10,
                'ai_requests_per_hour': 100,
                'allowed_signal_count': 5,
                'education_access_level': 1,
                'backtesting_enabled': True,
                'notifications_enabled': True,
            },
            'premium': {
                'signal_credits': -1,  # Unlimited
                'ai_requests_per_hour': 500,
                'allowed_signal_count': -1,  # Unlimited
                'education_access_level': 2,
                'backtesting_enabled': True,
                'portfolio_optimization_enabled': True,
                'custom_strategy_enabled': True,
                'priority_alerts': True,
                'webinar_credits': 2,
                'notifications_enabled': True,
            }
        }
    
    def create_subscription(
        self, 
        user_id: int, 
        tier: str,
        daily_access_hours: Optional[str] = None,  # Format: "HH:MM-HH:MM"
        symbols: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        capital: float = 1000.0,
    ) -> Subscription:
        """Create a new subscription for a user"""
        user = self.db.query(User).get(user_id)
        if not user:
            raise ValueError("User not found")
            
        features = self.tier_features.get(tier)
        if not features:
            raise ValueError(f"Invalid subscription tier: {tier}")
            
        # For free tier, set up trial period
        if tier == 'free':
            end_date = datetime.now(timezone.utc) + timedelta(days=features['trial_period_days'])
        else:
            end_date = datetime.now(timezone.utc) + timedelta(days=30)  # 30 days for paid tiers
        
        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            symbols=json.dumps(symbols or ["EURUSD"]),  # Default to EURUSD
            timeframes=json.dumps(timeframes or ["1H"]),  # Default to 1-hour timeframe
            capital=capital,
            start_date=datetime.now(timezone.utc),
            end_date=end_date,
            payment_status='pending',  # Will be updated after payment confirmation
            
            # Set up tier-specific features
            ai_consultation_enabled=True,
            signal_credits=features['signal_credits'],
            allowed_signal_count=features['allowed_signal_count'],
            education_access_level=features['education_access_level'],
            
            # For free tier
            trial_used=tier == 'free',
            daily_access_hours=daily_access_hours if tier == 'free' else None,
            
            # Premium features
            backtesting_enabled=features.get('backtesting_enabled', False),
            portfolio_optimization_enabled=features.get('portfolio_optimization_enabled', False),
            custom_strategy_enabled=features.get('custom_strategy_enabled', False),
            priority_alerts=features.get('priority_alerts', False),
            webinar_credits=features.get('webinar_credits', 0),
            
            # Additional settings
            notifications_enabled=features.get('notifications_enabled', True),
            risk_profile=user.risk_tolerance
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        # Update user's subscription status
        user.subscription_status = 'active'
        user.subscription_expiry = end_date
        self.db.commit()
        
        return subscription
    
    def update_subscription(
        self, 
        subscription_id: int, 
        **kwargs
    ) -> Optional[Subscription]:
        """Update an existing subscription"""
        subscription = self.db.query(Subscription).get(subscription_id)
        if not subscription:
            return None
            
        for key, value in kwargs.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)
                
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def cancel_subscription(self, subscription_id: int) -> bool:
        """Cancel a subscription"""
        subscription = self.db.query(Subscription).get(subscription_id)
        if not subscription:
            return False
            
        subscription.payment_status = 'cancelled'
        subscription.end_date = datetime.now(timezone.utc)
        
        # Update user's subscription status
        user = subscription.user
        user.subscription_status = 'inactive'
        user.subscription_expiry = None
        
        self.db.commit()
        return True
    
    def check_trial_eligibility(self, user_id: int) -> bool:
        """Check if user is eligible for free trial"""
        # Check if user has any previous trial subscriptions
        trial_sub = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.trial_used == True
        ).first()
        
        return trial_sub is None
    
    def validate_daily_access(self, subscription_id: int) -> bool:
        """Check if user has access during their selected hours (free tier)"""
        subscription = self.db.query(Subscription).get(subscription_id)
        if not subscription or subscription.tier != 'free':
            return True  # Non-free tiers always have access
            
        if not subscription.daily_access_hours:
            return False
            
        now = datetime.now(timezone.utc)
        try:
            start_time, end_time = subscription.daily_access_hours.split('-')
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            
            current_time = now.hour * 60 + now.minute
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            return start_minutes <= current_time <= end_minutes
        except:
            return False
    
    def check_signal_change_eligibility(self, subscription_id: int) -> Dict[str, Any]:
        """Check if user can make signal changes"""
        subscription = self.db.query(Subscription).get(subscription_id)
        if not subscription:
            return {"eligible": False, "reason": "Subscription not found"}
            
        # Premium tier has unlimited changes
        if subscription.tier == 'premium':
            return {"eligible": True, "remaining_changes": -1}
        
        # For other tiers, check credits
        if subscription.signal_changes_made >= subscription.signal_credits:
            return {
                "eligible": False,
                "reason": "No signal changes remaining",
                "remaining_changes": 0
            }
            
        remaining = subscription.signal_credits - subscription.signal_changes_made
        return {"eligible": True, "remaining_changes": remaining}
    
    def use_signal_change(self, subscription_id: int) -> bool:
        """Record a signal change usage"""
        subscription = self.db.query(Subscription).get(subscription_id)
        if not subscription:
            return False
            
        # Premium tier has unlimited changes
        if subscription.tier == 'premium':
            subscription.last_signal_change = datetime.now(timezone.utc)
            self.db.commit()
            return True
            
        if subscription.signal_changes_made >= subscription.signal_credits:
            return False
            
        subscription.signal_changes_made += 1
        subscription.last_signal_change = datetime.now(timezone.utc)
        self.db.commit()
        return True
