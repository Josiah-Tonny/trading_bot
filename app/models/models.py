from sqlalchemy import String, BigInteger, ForeignKey, DateTime, Boolean, Float, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
import os

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    # Modern SQLAlchemy 2.0 style with proper typing
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    username: Mapped[Optional[str]] = mapped_column(String(100))
    risk_tolerance: Mapped[str] = mapped_column(String(20), default='moderate')
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_status: Mapped[str] = mapped_column(String(20), default='inactive')
    subscription_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reset_token: Mapped[Optional[str]] = mapped_column(String(100))
    reset_token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or "Unknown User"

    def is_subscription_active(self) -> bool:
        return bool(self.subscription_status == 'active' and 
                self.subscription_expiry and 
                self.subscription_expiry > datetime.utcnow())

    def __repr__(self):
        return f'<User {self.email or self.telegram_user_id}>'

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    tier: Mapped[str] = mapped_column(String(50))
    symbols: Mapped[Optional[str]] = mapped_column(Text)
    timeframes: Mapped[Optional[str]] = mapped_column(Text)
    capital: Mapped[float] = mapped_column(Float, default=0.0)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    payment_status: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscriptions")

    def __repr__(self):
        return f'<Subscription {self.tier} for User {self.user_id}>'

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()