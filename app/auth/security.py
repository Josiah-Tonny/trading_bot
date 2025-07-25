"""Security utilities for authentication and user protection."""
import os
from typing import Optional, Union, Dict, TypedDict, Protocol, cast
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
import pyotp
from sqlalchemy import select, update, ForeignKey, String, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
import logging
from dataclasses import dataclass

from app.models.models import Base
from app.models.models import User

logger = logging.getLogger(__name__)

class LoginAttempt(Base):
    """Model for tracking login attempts"""
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    ip_address: Mapped[str] = mapped_column(String(45))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    success: Mapped[bool] = mapped_column(Boolean)

@dataclass
class AuthResponse:
    success: bool
    message: str
    user_id: Optional[int] = None
    token: Optional[str] = None

class SecurityProtocol(Protocol):
    """Protocol for security operations"""
    async def verify_password(self, password: str, password_hash: str) -> bool: ...
    async def hash_password(self, password: str) -> str: ...
    async def generate_otp_secret(self) -> str: ...
    async def verify_otp(self, secret: str, otp: str) -> bool: ...
    async def generate_token(self, user_id: int) -> str: ...
    async def verify_token(self, token: str) -> Optional[int]: ...
    async def track_login_attempt(self, user_id: Optional[int], ip_address: str, success: bool) -> None: ...

class SecurityService:
    """Implementation of security operations"""
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session
        self._max_attempts: int = 5
        self._lockout_duration: timedelta = timedelta(minutes=30)
        self._jwt_secret: str = os.getenv('JWT_SECRET_KEY', 'your-secret-key')

    async def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    async def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    async def generate_otp_secret(self) -> str:
        return pyotp.random_base32()

    async def verify_otp(self, secret: str, otp: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(otp)

    async def generate_token(self, user_id: int) -> str:
        payload: Dict[str, Union[int, datetime]] = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(days=1)
        }
        return jwt.encode(payload, self._jwt_secret, algorithm='HS256')

    async def verify_token(self, token: str) -> Optional[int]:
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=['HS256'])
            return payload.get('user_id')
        except jwt.InvalidTokenError:
            return None

    async def track_login_attempt(self, user_id: Optional[int], ip_address: str, success: bool) -> None:
        """Track login attempts for rate limiting and notifications"""
        attempt = LoginAttempt(
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc),
            success=success
        )
        self.session.add(attempt)
        await self.session.commit()

        if user_id and not success:
            # Check for multiple failed attempts
            stmt = select(LoginAttempt).where(
                LoginAttempt.user_id == user_id,
                LoginAttempt.success == False,
                LoginAttempt.timestamp > datetime.now(timezone.utc) - self._lockout_duration
            )
            result = await self.session.execute(stmt)
            failed_attempts = result.scalars().all()

            if len(failed_attempts) >= self._max_attempts:
                # Lock account and notify user
                stmt = update(User).where(User.id == user_id).values(
                    is_locked=True,
                    locked_until=datetime.now(timezone.utc) + self._lockout_duration
                )
                await self.session.execute(stmt)
                await self.session.commit()
                await self._notify_user_of_lockout(user_id)

    async def _notify_user_of_lockout(self, user_id: int, ip_address: str) -> None:
        """Notify user of account lockout via email and Telegram"""
        from app.notifications import get_notification_service
        from app.models.models import User

        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return

        notification_service = await get_notification_service(self.session)
        message = f"""
        🚨 Security Alert: Multiple failed login attempts detected on your Alpha Pro Trader account.
        Your account has been temporarily locked for {self._lockout_duration.seconds // 60} minutes.
        
        If this wasn't you, please:
        1. Change your password immediately
        2. Enable 2FA if not already enabled
        3. Contact support if you need assistance
        
        Time of incident: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
        """

        # Send notifications
        if user.email:
            await notification_service.send_email(
                to=user.email,
                subject="Security Alert - Account Locked",
                body=message
            )
        
        if user.telegram_user_id:
            await notification_service.send_telegram_message(
                user_id=user.telegram_user_id,
                message=message
            )
