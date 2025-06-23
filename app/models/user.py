from datetime import datetime, timedelta
import secrets
import random
import string
from typing import List, Optional, Dict, Any

class Subscription:
    def __init__(self, symbols: List[str], timeframes: List[str], capital: float) -> None:
        self.symbols = symbols
        self.timeframes = timeframes
        self.capital = capital

class User:
    def __init__(
        self,
        telegram_id: Optional[int] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_active: bool = False,
        subscription_expiry: Optional[datetime] = None,
        subscriptions: Optional[List[Subscription]] = None,
        reset_token: Optional[str] = None,
        reset_token_expiry: Optional[datetime] = None,
    ) -> None:
        self.telegram_id = telegram_id
        self.email = email
        self.password = password  # In production, store hashed!
        self.is_active = is_active
        self.subscription_expiry = subscription_expiry or None
        self.subscriptions = subscriptions or []
        self.reset_token = reset_token
        self.reset_token_expiry = reset_token_expiry

_users: Dict[Any, User] = {}

def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    for user in _users.values():
        if user.telegram_id == telegram_id:
            return user
    return None

def get_user_by_id(user_id: Any) -> Optional[User]:
    return _users.get(user_id)

def get_user_by_email(email: str) -> Optional[User]:
    for user in _users.values():
        if user.email == email:
            return user
    return None

def create_user(email: Optional[str] = None, password: Optional[str] = None, telegram_id: Optional[int] = None) -> User:
    user_id = telegram_id or email
    if user_id in _users:
        return _users[user_id]
    user = User(email=email, password=password, telegram_id=telegram_id)
    _users[user_id] = user
    return user

def activate_user_subscription(user_id: Any, duration_days: int = 30) -> Optional[User]:
    user = _users.get(user_id)
    if not user:
        return None
    user.is_active = True
    user.subscription_expiry = datetime.now() + timedelta(days=duration_days)
    user.subscriptions = [Subscription(symbols=["EURUSD"], timeframes=["1h"], capital=100)]
    return user

def set_password_reset_token(email: str) -> Optional[str]:
    user = get_user_by_email(email)
    if not user:
        return None
    otp = "APT" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    user.reset_token = otp
    user.reset_token_expiry = datetime.now() + timedelta(hours=1)
    return otp

def reset_password(token: str, new_password: str) -> bool:
    for user in _users.values():
        if user.reset_token == token and user.reset_token_expiry and user.reset_token_expiry > datetime.now():
            user.password = new_password
            user.reset_token = None
            user.reset_token_expiry = None
            return True
    return False
    return False
