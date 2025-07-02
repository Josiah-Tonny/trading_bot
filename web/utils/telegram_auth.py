import hashlib
import hmac
import time
from urllib.parse import unquote
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

def verify_telegram_auth(auth_data: Dict, bot_token: str) -> bool:
    """
    Verify Telegram authentication data
    Returns True if authentication is valid, False otherwise
    """
    if not auth_data.get('hash') or not bot_token:
        logger.warning("Missing hash or bot token for Telegram auth verification")
        return False
    
    # Make a copy to avoid modifying original data
    data_to_verify = auth_data.copy()
    received_hash = data_to_verify.pop('hash')
    
    # Remove None values and empty strings
    data_to_verify = {k: v for k, v in data_to_verify.items() if v is not None and v != ''}
    
    # Check auth_date (should be within last 24 hours)
    auth_date = data_to_verify.get('auth_date')
    if auth_date:
        try:
            auth_timestamp = int(auth_date)
            current_timestamp = int(time.time())
            # Allow 24 hours for auth (86400 seconds)
            if current_timestamp - auth_timestamp > 86400:
                logger.warning("Telegram auth data too old")
                return False
        except (ValueError, TypeError):
            logger.warning("Invalid auth_date in Telegram data")
            return False
    
    # Create data string for verification
    data_check_arr = []
    for key in sorted(data_to_verify.keys()):
        value = str(data_to_verify[key])
        data_check_arr.append(f"{key}={value}")
    
    data_check_string = '\n'.join(data_check_arr)
    
    # Create secret key
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    
    # Calculate hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare hashes
    is_valid = hmac.compare_digest(calculated_hash, received_hash)
    
    if not is_valid:
        logger.warning("Telegram auth hash verification failed")
        logger.debug(f"Expected: {calculated_hash}, Received: {received_hash}")
    
    return is_valid

def extract_telegram_user_data(auth_data: Dict) -> Dict:
    """
    Extract and clean user data from Telegram auth response
    """
    return {
        'telegram_user_id': int(auth_data.get('id', 0)),
        'first_name': unquote(auth_data.get('first_name', '')) if auth_data.get('first_name') else '',
        'last_name': unquote(auth_data.get('last_name', '')) if auth_data.get('last_name') else '',
        'telegram_username': unquote(auth_data.get('username', '')) if auth_data.get('username') else '',
        'profile_picture': unquote(auth_data.get('photo_url', '')) if auth_data.get('photo_url') else '',
        'auth_date': auth_data.get('auth_date')
    }