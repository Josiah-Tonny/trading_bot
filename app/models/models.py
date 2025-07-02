from sqlalchemy import String, BigInteger, ForeignKey, DateTime, Boolean, Float, Text, create_engine, text
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
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
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
                self.subscription_expiry > datetime.utcnow())

    def __repr__(self):
        identifier = self.email or self.telegram_user_id or self.username
        return f'<User {identifier}>'

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
# Go up 3 levels: models -> app -> trading_bot, then into web
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