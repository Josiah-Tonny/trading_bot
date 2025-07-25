"""Security-related database models."""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import DatabaseModel

class LoginAttempt(DatabaseModel):
    """Track login attempts for security monitoring"""
    __tablename__ = 'login_attempts'

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    ip_address: Mapped[str] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    user: Mapped['User'] = relationship(back_populates='login_attempts')

class SecurityAudit(DatabaseModel):
    """Audit log for security-related events"""
    __tablename__ = 'security_audits'

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    event_type: Mapped[str] = mapped_column(String(50))
    event_data: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[str] = mapped_column(String(45))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped['User'] = relationship(back_populates='security_audits')
