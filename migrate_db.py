#!/usr/bin/env python3
"""
Database migration script to add Telegram authentication support
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.models.models import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_user_table():
    """Add new columns for Telegram support"""
    
    migrations = [
        # Add registration_method column
        "ALTER TABLE users ADD COLUMN registration_method VARCHAR(20) DEFAULT 'email'",
        
        # Add profile_picture column for Telegram photo
        "ALTER TABLE users ADD COLUMN profile_picture VARCHAR(500)",
        
        # Add telegram_username column (different from regular username)
        "ALTER TABLE users ADD COLUMN telegram_username VARCHAR(100)",
        
        # Update existing users to have 'email' as registration method
        "UPDATE users SET registration_method = 'email' WHERE registration_method IS NULL",
        
        # Update existing Telegram users (if any) to have 'telegram' as registration method
        "UPDATE users SET registration_method = 'telegram' WHERE telegram_user_id IS NOT NULL",
    ]
    
    with engine.connect() as conn:
        for migration in migrations:
            try:
                logger.info(f"Executing: {migration}")
                conn.execute(text(migration))
                conn.commit()
                logger.info("✅ Migration successful")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info("⚠️  Column already exists, skipping...")
                else:
                    logger.error(f"❌ Migration failed: {e}")
                    raise

def verify_migration():
    """Verify that the migration was successful"""
    try:
        with engine.connect() as conn:
            # Test the new columns
            result = conn.execute(text("""
                SELECT registration_method, profile_picture, telegram_username 
                FROM users 
                LIMIT 1
            """))
            logger.info("✅ Migration verification successful - new columns accessible")
            return True
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting database migration for Telegram support...")
    
    try:
        migrate_user_table()
        if verify_migration():
            logger.info("🎉 Database migration completed successfully!")
        else:
            logger.error("💥 Migration verification failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        sys.exit(1)