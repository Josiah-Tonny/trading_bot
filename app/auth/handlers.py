"""Authentication handlers for both web and Telegram interfaces."""
from datetime import datetime, timezone
from typing import Optional, TypedDict, Tuple

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pyotp

from app.models.models import User
from app.auth.security import SecurityService, SecurityProtocol, AuthResponse
from app.database import get_session


class AuthData(TypedDict, total=False):
    """Authentication input data"""
    username: Optional[str]
    email: Optional[str]
    password: str
    telegram_id: Optional[int]
    otp_code: Optional[str]


class AuthHandler:
    """Handler for user authentication operations"""
    def __init__(self, session: AsyncSession) -> None:
        """Initialize auth handler with database session"""
        self.session: AsyncSession = session
        self.security: SecurityProtocol = SecurityService(session)
        self._cast_auth_response = AuthResponse  # For type checking

    def _get_str_value(self, auth_data: AuthData, key: str) -> Optional[str]:
        """Safely get string value from auth data"""
        value = auth_data.get(key)
        return str(value) if value is not None else None

    def _get_int_value(self, auth_data: AuthData, key: str) -> Optional[int]:
        """Safely get integer value from auth data"""
        value = auth_data.get(key)
        return int(value) if value is not None else None

    async def authenticate_user(self, auth_data: AuthData, ip_address: str) -> AuthResponse:
        """Authenticate user through any supported method"""
        # Find user by email, username, or telegram_id
        user = await self._get_user(auth_data)
        
        if not user:
            await self.security.track_login_attempt(None, ip_address, False)
            return AuthResponse(
                success=False,
                message="Invalid credentials",
                user_id=None,
                token=None
            )

        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.now(timezone.utc):
                return AuthResponse(
                    success=False, 
                    message=f"Account locked until {user.locked_until}",
                    user_id=None,
                    token=None
                )
            # Reset lock if time has expired
            user.is_locked = False
            user.locked_until = None
            await self.session.commit()

        # Verify password
        if 'password' not in auth_data or not await self.security.verify_password(auth_data['password'], user.password_hash):
            await self.security.track_login_attempt(user.id, ip_address, False)
            return AuthResponse(
                success=False,
                message="Invalid credentials",
                user_id=None,
                token=None
            )

        # Verify OTP if enabled
        if user.two_factor_enabled and 'otp_code' in auth_data and auth_data['otp_code']:
            if not user.otp_secret or not await self.security.verify_otp(user.otp_secret, auth_data['otp_code']):
                await self.security.track_login_attempt(user.id, ip_address, False)
                return AuthResponse(
                    success=False,
                    message="Invalid OTP code",
                    user_id=None,
                    token=None
                )

        # Generate JWT token
        token = await self.security.generate_token(user.id)
        await self.security.track_login_attempt(user.id, ip_address, True)

        return AuthResponse(
            success=True,
            message="Authentication successful",
            user_id=user.id,
            token=token
        )

    async def _get_user(self, auth_data: AuthData) -> Optional[User]:
        """Find user by any provided identifier"""
        # Construct query based on provided credentials
        query = select(User)
        conditions = []
        
        if 'email' in auth_data and auth_data['email']:
            conditions.append(User.email == auth_data['email'])
        if 'username' in auth_data and auth_data['username']:
            conditions.append(User.username == auth_data['username'])
        if 'telegram_id' in auth_data and auth_data['telegram_id'] is not None:
            conditions.append(User.telegram_id == auth_data['telegram_id'])
            
        if not conditions:
            return None
            
        query = query.where(*conditions)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def register_user(self, auth_data: AuthData) -> AuthResponse:
        """Register a new user"""
        # Check if user exists
        existing_user = await self._get_user(auth_data)
        if existing_user:
            return AuthResponse(
                success=False,
                message="User already exists",
                user_id=None,
                token=None
            )

        # Create new user
        if 'password' not in auth_data:
            return AuthResponse(
                success=False,
                message="Password is required",
                user_id=None,
                token=None
            )
            
        password_hash = await self.security.hash_password(auth_data['password'])
        new_user = User(
            username=auth_data.get('username'),
            email=auth_data.get('email'),
            telegram_id=auth_data.get('telegram_id'),
            password_hash=password_hash,
            two_factor_enabled=False,
            is_active=True
        )
        self.session.add(new_user)
        await self.session.commit()

        # Generate JWT token
        token = await self.security.generate_token(new_user.id)
        return AuthResponse(
            success=True,
            message="Registration successful",
            user_id=new_user.id,
            token=token
        )

    async def setup_2fa(self, user_id: int) -> Tuple[str, str]:
        """Set up 2FA for a user"""
        user = await self.session.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        secret = await self.security.generate_otp_secret()
        user.otp_secret = secret
        user.two_factor_enabled = True
        await self.session.commit()

        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            user.email or user.username or f"user_{user.id}",
            issuer_name="Alpha Pro Trader"
        )

        return secret, provisioning_uri


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session)
) -> User:
    """FastAPI dependency for getting current authenticated user"""
    auth_header = str(request.headers.get('Authorization', ''))
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(' ')[1]
    security = SecurityService(session)
    user_id = await security.verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
