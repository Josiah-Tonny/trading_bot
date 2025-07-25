"""Common types used throughout the application."""
from typing import NewType, TypedDict, Optional

# Type aliases
UserId = NewType('UserId', int)
TelegramId = NewType('TelegramId', int)

class AuthData(TypedDict, total=False):
    """Authentication input data."""
    username: Optional[str]
    email: Optional[str]
    password: str
    telegram_id: Optional[int] 
    otp_code: Optional[str]

class TokenPayload(TypedDict):
    """JWT token payload."""
    user_id: UserId
    exp: float
