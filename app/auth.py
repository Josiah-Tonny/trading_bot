from app.models.user import (
    create_user,
    get_user_by_email,
    get_user_by_telegram_id,
    reset_password,
    set_password_reset_token,
    User,
)
from typing import Optional, Dict, Any
import hashlib


def authenticate(
    email: Optional[str] = None,
    password: Optional[str] = None,
    telegram_profile: Optional[Dict[str, Any]] = None
) -> Optional[User]:
    if telegram_profile:
        telegram_id = telegram_profile["id"]
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            user = create_user(telegram_id=telegram_id, username=telegram_profile.get("username"))
        return user
    elif email and password:
        user = get_user_by_email(email)
        # Fix password checking to use hash
        if user and hasattr(user, 'password_hash') and user.password_hash == _hash_password(password):
            return user
        # Fallback for plain text passwords (remove in production)
        elif user and hasattr(user, 'password') and user.password == password:
            return user
    return None


def _hash_password(password: str) -> str:
    """Hash password using SHA-256 (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def forgot_password(email: str) -> Optional[str]:
    otp = set_password_reset_token(email)
    if otp:
        # In production, send OTP via email or SMS
        return otp
    return None


def perform_password_reset(token: str, new_password: str) -> bool:
    return reset_password(token, new_password)