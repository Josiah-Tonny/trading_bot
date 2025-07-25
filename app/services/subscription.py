from enum import Enum
from typing import Dict, List, TypedDict, Optional
from decimal import Decimal

class SubscriptionFeatures(TypedDict, total=False):
    """Features available for each subscription tier"""
    sentiment_analysis: bool
    basic_signals: bool
    advanced_signals: Optional[bool]
    risk_analysis: bool
    portfolio_optimization: bool
    custom_strategy: Optional[bool]
    educational_content: List[str]
    educational_webinars: bool
    custom_signals_per_day: int
    api_requests_per_hour: int
    signal_change_fee: Decimal

class SubscriptionTier(str, Enum):
    """Available subscription tiers"""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

# Feature sets for each tier
TIER_FEATURES: Dict[str, SubscriptionFeatures] = {
    "free": {
        "sentiment_analysis": True,
        "basic_signals": True,
        "advanced_signals": False,
        "risk_analysis": False,
        "portfolio_optimization": False,
        "custom_strategy": False,
        "educational_content": ["beginner"],
        "educational_webinars": False,
        "custom_signals_per_day": 1,
        "api_requests_per_hour": 10,
        "signal_change_fee": Decimal("3.00")
    },
    "pro": {
        "sentiment_analysis": True,
        "basic_signals": True,
        "advanced_signals": True,
        "risk_analysis": True,
        "portfolio_optimization": False,
        "custom_strategy": False,
        "educational_content": ["beginner", "intermediate"],
        "educational_webinars": True,
        "custom_signals_per_day": 5,
        "api_requests_per_hour": 100,
        "signal_change_fee": Decimal("1.50")
    },
    "premium": {
        "sentiment_analysis": True,
        "basic_signals": True,
        "advanced_signals": True,
        "risk_analysis": True,
        "portfolio_optimization": True,
        "custom_strategy": True,
        "educational_content": ["beginner", "intermediate", "advanced", "expert"],
        "educational_webinars": True,
        "custom_signals_per_day": float('inf'),
        "api_requests_per_hour": 500,
        "signal_change_fee": Decimal("0.00")
    }
}

# Usage limits for each tier
TIER_USAGE_LIMITS = {
    "free": {
        "content_access_daily": 5,
        "signal_generation_daily": 3,
        "api_requests_hourly": 10
    },
    "pro": {
        "content_access_daily": 20,
        "signal_generation_daily": 10,
        "api_requests_hourly": 100
    },
    "premium": {
        "content_access_daily": float('inf'),
        "signal_generation_daily": float('inf'),
        "api_requests_hourly": 500
    }
}

class SubscriptionService:
    """Service for managing subscription tiers and features"""
    
    @staticmethod
    def get_features(tier: str) -> SubscriptionFeatures:
        """Get features for a subscription tier"""
        return TIER_FEATURES.get(tier, TIER_FEATURES["free"])
    
    @staticmethod
    def get_usage_limits(tier: str) -> dict:
        """Get usage limits for a subscription tier"""
        return TIER_USAGE_LIMITS.get(tier, TIER_USAGE_LIMITS["free"])
    
    @staticmethod
    def can_access_feature(tier: str, feature: str) -> bool:
        """Check if a tier has access to a feature"""
        features = TIER_FEATURES.get(tier, TIER_FEATURES["free"])
        return bool(features.get(feature, False))
    
    @staticmethod
    def can_access_content_level(tier: str, level: str) -> bool:
        """Check if a tier has access to an educational content level"""
        features = TIER_FEATURES.get(tier, TIER_FEATURES["free"])
        return level in features["educational_content"]
