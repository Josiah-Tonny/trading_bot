from typing import List
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)
    subscription_status = Column(String, default='inactive')
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    subscription_expiry = Column(DateTime, nullable=True)
    # ...other fields...

    subscriptions = relationship("Subscription", order_by="Subscription.id", back_populates="user")
    payments = relationship("Payment", order_by="Payment.id", back_populates="user")
    trade_logs = relationship("TradeLog", order_by="TradeLog.id", back_populates="user")
    signals = relationship("Signal", order_by="Signal.id", back_populates="user")

    def is_active(self):
        return self.subscription_status == 'active' and (self.subscription_expiry is None or self.subscription_expiry > datetime.utcnow())

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    tier = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    payment_status = Column(String)
    # ...existing code...

    user = relationship("User", back_populates="subscriptions")

class Signal(Base):
    __tablename__ = 'signals'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    symbol = Column(String)
    timeframe = Column(String)
    entry = Column(Float)
    tp = Column(Float)
    sl = Column(Float)
    risk = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="signals")
    trade_logs = relationship("TradeLog", order_by="TradeLog.id", back_populates="signal")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    type = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")

class TradeLog(Base):
    __tablename__ = 'trade_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    signal_id = Column(Integer, ForeignKey('signals.id'))
    executed_at = Column(DateTime, default=datetime.utcnow)
    result = Column(String)

    user = relationship("User", back_populates="trade_logs")
    signal = relationship("Signal", back_populates="trade_logs")