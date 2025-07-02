#!/usr/bin/env python3
"""
Initialize database with all tables including Telegram support
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.models import create_tables, test_connection, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with all tables"""
    try:
        logger.info("🔍 Testing database connection...")
        if not test_connection():
            logger.error("❌ Database connection failed!")
            return False
        
        logger.info("🏗️  Creating all tables...")
        success = create_tables()
        
        if success:
            logger.info("✅ Tables created successfully!")
            
            # Verify tables exist
            with engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result]
                logger.info(f"📋 Created tables: {tables}")
                
                # Check users table structure
                if 'users' in tables:
                    result = conn.execute(text("PRAGMA table_info(users)"))
                    columns = [row[1] for row in result]
                    logger.info(f"👤 Users table columns: {columns}")
                    
                    # Check if new Telegram columns exist
                    telegram_columns = ['registration_method', 'profile_picture', 'telegram_username']
                    missing_columns = [col for col in telegram_columns if col not in columns]
                    
                    if missing_columns:
                        logger.warning(f"⚠️  Missing Telegram columns: {missing_columns}")
                        logger.info("🔧 Adding missing columns...")
                        
                        for col in missing_columns:
                            if col == 'registration_method':
                                conn.execute(text("ALTER TABLE users ADD COLUMN registration_method VARCHAR(20) DEFAULT 'email'"))
                            elif col == 'profile_picture':
                                conn.execute(text("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(500)"))
                            elif col == 'telegram_username':
                                conn.execute(text("ALTER TABLE users ADD COLUMN telegram_username VARCHAR(100)"))
                        
                        conn.commit()
                        logger.info("✅ Missing columns added!")
                    else:
                        logger.info("✅ All Telegram columns present!")
            
            return True
        else:
            logger.error("❌ Failed to create tables!")
            return False
            
    except Exception as e:
        logger.error(f"💥 Database initialization failed: {e}")
        return False

def test_user_creation():
    """Test creating both email and Telegram users"""
    try:
        from app.models.user import UserService
        
        logger.info("🧪 Testing user creation...")
        
        with UserService() as service:
            # Test email user
            try:
                email_user = service.create_user(
                    email="test@example.com",
                    password="testpass123",
                    first_name="Test",
                    last_name="User",
                    username="testuser"
                )
                logger.info(f"✅ Email user created: {email_user.id}")
                
                # Clean up
                service.db.delete(email_user)
                service.db.commit()
                
            except Exception as e:
                logger.error(f"❌ Email user creation failed: {e}")
                return False
            
            # Test Telegram user
            try:
                telegram_data = {
                    'telegram_user_id': 123456789,
                    'first_name': 'Telegram',
                    'last_name': 'User',
                    'telegram_username': 'telegramuser'
                }
                
                telegram_user = service.create_telegram_user(telegram_data)
                logger.info(f"✅ Telegram user created: {telegram_user.id}")
                
                # Clean up
                service.db.delete(telegram_user)
                service.db.commit()
                
            except Exception as e:
                logger.error(f"❌ Telegram user creation failed: {e}")
                return False
        
        logger.info("🎉 All user creation tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"💥 User creation test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Initializing database for TradePro...")
    
    if init_database():
        logger.info("✅ Database initialized successfully!")
        
        if test_user_creation():
            logger.info("🎉 All tests passed! Database is ready for Telegram authentication!")
        else:
            logger.error("💥 User creation tests failed!")
            sys.exit(1)
    else:
        logger.error("💥 Database initialization failed!")
        sys.exit(1)