from sqlalchemy.orm import Session
from app.models.models import User, Subscription, SessionLocal
from typing import Optional, List
from datetime import datetime, timedelta
import json
import hashlib
import secrets
import string

class UserService:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.telegram_user_id == telegram_id).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, email: Optional[str] = None, password: Optional[str] = None, 
                   telegram_id: Optional[int] = None, **kwargs) -> User:
        # Check if user already exists
        if email:
            existing_user = self.get_user_by_email(email)
            if existing_user:
                raise ValueError("User with this email already exists")

        if telegram_id:
            existing_user = self.get_user_by_telegram_id(telegram_id)
            if existing_user:
                return existing_user  # Return existing Telegram user

        # Create new user
        user = User(
            email=email.lower() if email else None,
            password_hash=self._hash_password(password) if password else None,
            telegram_user_id=telegram_id,
            **kwargs
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def activate_user_subscription(self, user_id: int, duration_days: int = 30) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.is_active = True
        user.subscription_status = 'active'
        user.subscription_expiry = datetime.utcnow() + timedelta(days=duration_days)
        
        # Create subscription record
        subscription = Subscription(
            user_id=user.id,
            tier='basic',
            symbols=json.dumps(["EURUSD"]),
            timeframes=json.dumps(["1h"]),
            capital=100.0,
            end_date=user.subscription_expiry,
            payment_status='completed'
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_password_reset_token(self, email: str) -> Optional[str]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        token = "APT" + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        
        self.db.commit()
        return token

    def reset_password(self, token: str, new_password: str) -> bool:
        user = self.db.query(User).filter(
            User.reset_token == token,
            User.reset_token_expiry > datetime.utcnow()
        ).first()
        
        if user:
            user.password_hash = self._hash_password(new_password)
            user.reset_token = None
            user.reset_token_expiry = None
            self.db.commit()
            return True
        return False

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if user and user.password_hash == self._hash_password(password):
            return user
        return None

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (use bcrypt in production)"""
        return hashlib.sha256(password.encode()).hexdigest()

# Convenience functions for backward compatibility
def get_user_by_email(email: str) -> Optional[User]:
    with UserService() as service:
        return service.get_user_by_email(email)

def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    with UserService() as service:
        return service.get_user_by_telegram_id(telegram_id)

def create_user(email: Optional[str] = None, password: Optional[str] = None, 
               telegram_id: Optional[int] = None, **kwargs) -> User:
    with UserService() as service:
        return service.create_user(email, password, telegram_id, **kwargs)

def activate_user_subscription(user_id: int, duration_days: int = 30) -> Optional[User]:
    with UserService() as service:
        return service.activate_user_subscription(user_id, duration_days)
