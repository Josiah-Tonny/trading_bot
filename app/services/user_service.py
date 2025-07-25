from sqlalchemy.orm import Session
from app.models.models import User, Subscription
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import json
import hashlib
import secrets
import string
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    async def create_user(self, username: str, password: str, email: str) -> User:
        """Create a new user"""
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user
        user = User(
            username=username,
            password_hash=password_hash,
            email=email,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user attributes"""
        user = await self.get_user(user_id)
        if not user:
            return None
            
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
                
        self.db.commit()
        self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        user = await self.get_user(user_id)
        if not user:
            return False
            
        self.db.delete(user)
        self.db.commit()
        return True

    async def verify_password(self, user: User, password: str) -> bool:
        """Verify user password"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return user.password_hash == password_hash

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = await self.get_user(user_id)
        if not user or not await self.verify_password(user, old_password):
            return False
            
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        user.password_hash = password_hash
        self.db.commit()
        return True

    async def reset_password(self, user_id: int) -> Optional[str]:
        """Reset user password and return new password"""
        user = await self.get_user(user_id)
        if not user:
            return None
            
        # Generate random password
        alphabet = string.ascii_letters + string.digits
        new_password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Update password
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        user.password_hash = password_hash
        self.db.commit()
        
        return new_password
