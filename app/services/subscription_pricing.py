from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from decimal import Decimal

class SubscriptionPricing:
    """
    Subscription pricing configuration that factors in AI API costs
    """
    
    TIERS = {
        'free': {
            'price': Decimal('0.00'),
            'ai_requests_per_hour': 10,
            'signal_changes': 0,
            'signal_change_fee': Decimal('3.00'),
            'duration_days': 14,  # Trial period
            'features': {
                'basic_indicators': True,
                'ai_consultation': False,
                'custom_signals': 1,
                'random_signals': 2,
                'daily_hours': 4
            }
        },
        'pro': {
            'price': Decimal('29.99'),
            'ai_requests_per_hour': 100,
            'signal_changes': 10,
            'signal_change_fee': Decimal('1.50'),
            'duration_days': 30,
            'features': {
                'basic_indicators': True,
                'advanced_indicators': True,
                'ai_consultation': True,
                'custom_signals': 5,
                'daily_hours': 24,
                'risk_management': True,
                'educational_resources': True
            }
        },
        'premium': {
            'price': Decimal('99.99'),
            'ai_requests_per_hour': 500,
            'signal_changes': float('inf'),  # Unlimited
            'signal_change_fee': Decimal('0.00'),
            'duration_days': 30,
            'features': {
                'basic_indicators': True,
                'advanced_indicators': True,
                'ai_consultation': True,
                'portfolio_optimization': True,
                'custom_signals': float('inf'),  # Unlimited
                'daily_hours': 24,
                'priority_alerts': True,
                'risk_management': True,
                'educational_resources': True,
                'strategy_builder': True,
                'one_on_one': True
            }
        }
    }

    @classmethod
    def get_tier_details(cls, tier: str) -> Dict:
        """Get the pricing and feature details for a subscription tier"""
        return cls.TIERS.get(tier, {})

    @classmethod
    def calculate_signal_change_fee(cls, tier: str) -> Decimal:
        """Calculate the fee for changing signals based on the subscription tier"""
        return cls.TIERS.get(tier, {}).get('signal_change_fee', Decimal('3.00'))

    @classmethod
    def get_ai_request_limit(cls, tier: str) -> int:
        """Get the AI API request limit for a subscription tier"""
        return cls.TIERS.get(tier, {}).get('ai_requests_per_hour', 0)
