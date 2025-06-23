from typing import List
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)
    subscription_status = Column(String, default='inactive')
    subscription_expiry = Column(DateTime, nullable=True)
    # ...other fields...

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

User.subscriptions = relationship("Subscription", order_by=Subscription.id, back_populates="user")