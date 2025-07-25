from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Union, cast, TypedDict
import redis
from redis import Redis
from sqlalchemy.orm import Session
from app.models.models import Subscription

class SessionDataDict(TypedDict):
    user_id: int
    subscription_tier: str
    start_time: str
    last_activity: str
    active: bool

SessionData = Dict[str, Union[str, int, bool, None]]
import os
import json
from redis import Redis
from sqlalchemy.orm import Session
from app.models.models import User, Subscription

class SessionTrackingService:
    def __init__(self, db: Session):
        self.db = db
        self.redis: Redis[bytes] = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        self.session_prefix = 'trading_session:'
        self.access_prefix = 'access_window:'
        
    def start_session(self, user_id: int) -> Dict[str, Any]:
        """Start a new trading session for a user"""
        # Get user's active subscription
        subscription = self.db.query(Subscription)\
            .filter(Subscription.user_id == user_id)\
            .filter(Subscription.end_date > datetime.now(timezone.utc))\
            .first()
            
        if not subscription:
            return {
                'success': False,
                'error': 'No active subscription found'
            }
            
        now = datetime.now(timezone.utc)
        
        # For free tier, validate access hours
        if subscription.tier == 'free':
            if not self._validate_access_window(subscription):
                next_window = self._get_next_access_window(subscription)
                return {
                    'success': False,
                    'error': 'Outside access hours',
                    'next_window': next_window.isoformat() if next_window else None
                }
        
        # Create session record
        session_data: SessionDataDict = {
            'user_id': user_id,
            'subscription_tier': subscription.tier,
            'start_time': now.isoformat(),
            'last_activity': now.isoformat(),
            'active': True
        }
        
        session_key = f"{self.session_prefix}{user_id}"
        self.redis.setex(
            name=session_key,
            time=int(timedelta(hours=4 if subscription.tier == 'free' else 24).total_seconds()),
            value=json.dumps(session_data)
        )
        
        return {
            'success': True,
            'session': session_data
        }
    
    def end_session(self, user_id: int) -> Dict[str, Any]:
        """End a user's trading session"""
        session_key = f"{self.session_prefix}{user_id}"
        session_data = self.redis.get(session_key)
        
        if not session_data:
            return {
                'success': False,
                'error': 'No active session found'
            }
            
        # Clean up session
        self.redis.delete(session_key)
        
        return {
            'success': True
        }
    
    def check_session(self, user_id: int) -> Dict[str, Any]:
        """Check if user has an active session"""
        session_key = f"{self.session_prefix}{user_id}"
        session_bytes = self.redis.get(session_key)
        
        if not session_bytes:
            return {
                'active': False
            }
            
        session: SessionData = json.loads(session_bytes.decode('utf-8'))
        
        # Update last activity
        session['last_activity'] = datetime.now(timezone.utc).isoformat()
        self.redis.setex(
            session_key,
            timedelta(hours=4 if session['subscription_tier'] == 'free' else 24),
            json.dumps(session)
        )
        
        return {
            'active': True,
            'session': session
        }
    
    def _validate_access_window(self, subscription: Subscription) -> bool:
        """Check if current time is within user's chosen access hours"""
        if not subscription.daily_access_hours:
            return False
            
        try:
            now = datetime.now(timezone.utc)
            start_time, end_time = subscription.daily_access_hours.split('-')
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            
            current_time = now.hour * 60 + now.minute
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            return start_minutes <= current_time <= end_minutes
            
        except:
            return False
    
    def _get_next_access_window(self, subscription: Subscription) -> Optional[datetime]:
        """Calculate the next available access window"""
        if not subscription.daily_access_hours:
            return None
            
        try:
            now = datetime.now(timezone.utc)
            start_time, _ = subscription.daily_access_hours.split('-')
            start_hour, start_minute = map(int, start_time.split(':'))
            
            next_window = now.replace(hour=start_hour, minute=start_minute)
            
            if next_window < now:
                next_window = next_window + timedelta(days=1)
                
            return next_window
            
        except:
            return None
    
    def get_session_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics about user's trading sessions"""
        subscription = self.db.query(Subscription)\
            .filter(Subscription.user_id == user_id)\
            .filter(Subscription.end_date > datetime.now(timezone.utc))\
            .first()
            
        if not subscription:
            return {
                'error': 'No active subscription found'
            }
            
        session_key = f"{self.session_prefix}{user_id}"
        session_bytes = self.redis.get(session_key)
        
        if not session_bytes:
            return {
                'active_session': False,
                'subscription_tier': subscription.tier,
                'daily_access_hours': subscription.daily_access_hours,
                'time_remaining': None
            }
            
        session: SessionData = json.loads(session_bytes.decode('utf-8'))
        start_time = datetime.fromisoformat(cast(str, session['start_time']))
        now = datetime.now(timezone.utc)
        
        # Calculate remaining time
        if subscription.tier == 'free':
            hours_used = (now - start_time).total_seconds() / 3600
            time_remaining = max(4 - hours_used, 0)  # 4 hours for free tier
        else:
            time_remaining = -1  # Unlimited for paid tiers
            
        return {
            'active_session': True,
            'subscription_tier': subscription.tier,
            'session_start': session['start_time'],
            'last_activity': session['last_activity'],
            'daily_access_hours': subscription.daily_access_hours,
            'time_remaining': time_remaining
        }
