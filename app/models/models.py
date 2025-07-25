from sqlalchemy import String, BigInteger, ForeignKey, DateTime, Boolean, Float, Text, Integer, create_engine, text
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
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
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    otp_secret: Mapped[Optional[str]] = mapped_column(String(32))
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_tolerance: Mapped[str] = mapped_column(String(20), default='moderate')
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_status: Mapped[str] = mapped_column(String(20), default='inactive')
    subscription_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reset_token: Mapped[Optional[str]] = mapped_column(String(100))
    reset_token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Add these new fields for Telegram support
    registration_method: Mapped[str] = mapped_column(String(20), default='email')  # 'email' or 'telegram'
    profile_picture: Mapped[Optional[str]] = mapped_column(String(500))  # Telegram photo URL
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100))  # Telegram @username
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        return (
            self.subscription_status == 'active' and
            bool(self.subscriptions) and
            any(s.tier == 'premium' for s in self.subscriptions)
        )
        
    @property
    def full_name(self) -> str:
        """Get user's full name or username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return self.username
        return f"User {self.id}"
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.telegram_username or "Unknown User"

    @property
    def display_name(self) -> str:
        """Get the best display name for the user"""
        if self.first_name:
            return self.full_name
        elif self.telegram_username:
            return f"@{self.telegram_username}"
        elif self.username:
            return self.username
        elif self.email:
            return self.email.split('@')[0]
        else:
            return f"User {self.id}"

    def is_subscription_active(self) -> bool:
        return bool(self.subscription_status == 'active' and 
                self.subscription_expiry and 
                self.subscription_expiry > datetime.now(timezone.utc))

    def __repr__(self):
        identifier = self.email or self.telegram_user_id or self.username
        return f'<User {identifier}>'

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    tier: Mapped[str] = mapped_column(String(50))  # 'free', 'pro', 'premium'
    symbols: Mapped[Optional[str]] = mapped_column(Text)  # JSON list of subscribed symbols
    timeframes: Mapped[Optional[str]] = mapped_column(Text)  # JSON list of subscribed timeframes
    capital: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Subscription timing
    start_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    payment_status: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Free tier specific fields
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_access_hours: Mapped[Optional[str]] = mapped_column(String(50))  # Format: "HH:MM-HH:MM"
    daily_access_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    daily_access_end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # AI consultation related fields
    ai_consultation_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_requests_count: Mapped[int] = mapped_column(Integer, default=0)
    last_ai_request: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Signal management
    signal_credits: Mapped[int] = mapped_column(Integer, default=0)  # Available signal changes
    signal_changes_made: Mapped[int] = mapped_column(Integer, default=0)  # Count of signal changes made
    last_signal_change: Mapped[Optional[datetime]] = mapped_column(DateTime)
    allowed_signal_count: Mapped[int] = mapped_column(Integer, default=1)  # Number of custom signals allowed
    
    # Features and settings
    features: Mapped[Optional[str]] = mapped_column(Text)  # JSON string of enabled features
    risk_profile: Mapped[str] = mapped_column(String(20), default='moderate')  # User's risk tolerance for signals
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Educational access (Pro/Premium)
    education_access_level: Mapped[int] = mapped_column(Integer, default=0)  # 0: None, 1: Basic, 2: Advanced
    webinar_credits: Mapped[int] = mapped_column(Integer, default=0)  # For premium tier live sessions
    
    # Trading features
    backtesting_enabled: Mapped[bool] = mapped_column(Boolean, default=False)  # For premium tier
    portfolio_optimization_enabled: Mapped[bool] = mapped_column(Boolean, default=False)  # For premium tier
    custom_strategy_enabled: Mapped[bool] = mapped_column(Boolean, default=False)  # For premium tier
    priority_alerts: Mapped[bool] = mapped_column(Boolean, default=False)  # For premium tier
    
    # Relationship
    user: Mapped["User"] = relationship(back_populates="subscriptions")

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscriptions")

    def __repr__(self):
        return f'<Subscription {self.tier} for User {self.user_id}>'

class Payment(Base):
    __tablename__ = 'payments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    amount: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(50))  # subscription, signal_change, etc.
    status: Mapped[str] = mapped_column(String(20))  # completed, pending, failed
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    payment_method: Mapped[str] = mapped_column(String(50))  # stripe, mpesa, etc.
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    provider_response: Mapped[Optional[str]] = mapped_column(Text)  # Store provider's response

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'web', 'trading_bot.db')
DATABASE_URL = f"sqlite:///{db_path}"

# Initialize global variables
engine = None
SessionLocal = None

def create_tables():
    """Create all tables"""
    if engine is None:
        print("❌ Cannot create tables - database not initialized")
        return False
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def get_db():
    """Get database session"""
    if SessionLocal is None:
        print("❌ Cannot get database session - database not initialized")
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

# Initialize database
try:
    engine = create_engine(DATABASE_URL, echo=False)  # Set echo=False to reduce noise
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"❌ Database setup failed: {e}")
    engine = None
    SessionLocal = None