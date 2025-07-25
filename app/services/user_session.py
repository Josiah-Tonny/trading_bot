from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.models import User, Subscription

class UserSessionService:
    def __init__(self, db: Session):
        self.db = db
        
    def check_user_access(self, user_id: int) -> Dict[str, bool | str]:
        """Check if user has access based on their subscription and daily time limit"""
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.end_date > datetime.utcnow()
        ).first()
        
        if not subscription:
            return {"allowed": False, "message": "No active subscription"}
            
        # Pro and Premium users have 24/7 access
        if subscription.tier in ['pro', 'premium']:
            return {"allowed": True, "message": "Full access"}
            
        # For free tier users, check their daily access window
        if subscription.tier == 'free':
            if not subscription.daily_access_hours:
                return {"allowed": False, "message": "Daily access hours not set"}
                
            now = datetime.now()
            start_time, end_time = subscription.daily_access_hours.split("-")
            
            # Convert time strings to datetime objects for comparison
            today = now.date()
            access_start = datetime.combine(today, datetime.strptime(start_time, "%H:%M").time())
            access_end = datetime.combine(today, datetime.strptime(end_time, "%H:%M").time())
            
            if access_start <= now <= access_end:
                return {"allowed": True, "message": "Within access hours"}
            else:
                next_start = access_start + timedelta(days=1) if now > access_end else access_start
                return {
                    "allowed": False,
                    "message": f"Outside access hours. Next window starts at {next_start.strftime('%H:%M')}"
                }
                
        return {"allowed": False, "message": "Invalid subscription tier"}
        
    def set_access_hours(self, user_id: int, start_time: str, end_time: str) -> Dict[str, bool | str]:
        """Set or update user's preferred access hours for free tier"""
        try:
            # Validate time format
            datetime.strptime(start_time, "%H:%M")
            datetime.strptime(end_time, "%H:%M")
            
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.tier == 'free'
            ).first()
            
            if not subscription:
                return {"success": False, "message": "No free tier subscription found"}
                
            # Calculate 4-hour window
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            duration = (end_dt - start_dt).seconds / 3600
            
            if duration != 4:
                return {"success": False, "message": "Access window must be exactly 4 hours"}
                
            subscription.daily_access_hours = f"{start_time}-{end_time}"
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Access hours set to {start_time}-{end_time}"
            }
            
        except ValueError:
            return {"success": False, "message": "Invalid time format. Use HH:MM"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": str(e)}
            
    def get_remaining_time(self, user_id: int) -> Dict[str, int | str]:
        """Get remaining time in user's daily access window"""
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.tier == 'free'
        ).first()
        
        if not subscription or not subscription.daily_access_hours:
            return {"minutes": 0, "message": "No access window set"}
            
        now = datetime.now()
        _, end_time = subscription.daily_access_hours.split("-")
        end_dt = datetime.combine(now.date(), datetime.strptime(end_time, "%H:%M").time())
        
        if now > end_dt:
            return {"minutes": 0, "message": "Access window ended for today"}
            
        remaining_minutes = int((end_dt - now).total_seconds() / 60)
        return {
            "minutes": remaining_minutes,
            "message": f"{remaining_minutes} minutes remaining in today's access window"
        }
