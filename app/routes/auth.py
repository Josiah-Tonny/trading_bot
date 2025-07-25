"""FastAPI routes for authentication and security."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.handlers import AuthHandler, AuthResponse
from app.auth.security import SecurityService
from app.database import get_session
from app.models.user import User

# Type aliases
JsonResponse = Dict[str, Any]

router: APIRouter = APIRouter()
oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get current user from token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Get current user from JWT token"""
    security = SecurityService(session)
    user_id = await security.verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

class LoginRequest(BaseModel):
    """Login request data model"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None
    password: str
    otp_code: Optional[str] = None

class RegisterRequest(BaseModel):
    """Registration request data model"""
    username: str
    email: EmailStr
    password: str
    telegram_id: Optional[int] = None

class Enable2FAResponse(BaseModel):
    """2FA setup response"""
    secret: str
    qr_uri: str

@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session)
) -> AuthResponse:
    """Login endpoint supporting multiple authentication methods"""
    auth_handler = AuthHandler(session)
    client_ip = request.client.host if request.client else "unknown"
    
    auth_data = {
        'username': login_data.username,
        'email': login_data.email,
        'telegram_id': login_data.telegram_id,
        'password': login_data.password,
        'otp_code': login_data.otp_code
    }
    
    result = await auth_handler.authenticate_user(auth_data, client_ip)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message
        )
    
    return result

@router.post("/register", response_model=AuthResponse)
async def register(
    request: Request,
    register_data: RegisterRequest,
    session: AsyncSession = Depends(get_session)
) -> AuthResponse:
    """Register a new user"""
    auth_handler = AuthHandler(session)
    
    auth_data = {
        'username': register_data.username,
        'email': register_data.email,
        'password': register_data.password,
        'telegram_id': register_data.telegram_id
    }
    
    result = await auth_handler.register_user(auth_data)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return result

@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Enable2FAResponse:
    """Enable 2FA for current user"""
    auth_handler = AuthHandler(session)
    secret, uri = await auth_handler.setup_2fa(current_user.id)
    
    return Enable2FAResponse(
        secret=secret,
        qr_uri=uri
    )

@router.post("/2fa/verify", response_model=JsonResponse)
async def verify_2fa(
    otp_code: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> JsonResponse:
    """Verify 2FA code.
    Returns:
        A dictionary with key 'verified' and boolean value indicating success
    """
    security = SecurityService(session)
    if not hasattr(current_user, 'otp_secret') or not current_user.otp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not enabled"
        )
    
    is_valid = await security.verify_otp(current_user.otp_secret, otp_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    return {"verified": True}
