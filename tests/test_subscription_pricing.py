import pytest
from decimal import Decimal
from app.services.subscription_pricing import SubscriptionPricing

def test_free_tier_details():
    details = SubscriptionPricing.get_tier_details('free')
    assert details['price'] == Decimal('0.00')
    assert details['ai_requests_per_hour'] == 10
    assert details['signal_changes'] == 0
    assert details['signal_change_fee'] == Decimal('3.00')
    assert details['duration_days'] == 14
    assert details['features']['custom_signals'] == 1
    assert details['features']['random_signals'] == 2
    assert details['features']['daily_hours'] == 4
    assert not details['features']['ai_consultation']

def test_pro_tier_details():
    details = SubscriptionPricing.get_tier_details('pro')
    assert details['price'] == Decimal('29.99')
    assert details['ai_requests_per_hour'] == 100
    assert details['signal_changes'] == 10
    assert details['signal_change_fee'] == Decimal('1.50')
    assert details['duration_days'] == 30
    assert details['features']['custom_signals'] == 5
    assert details['features']['daily_hours'] == 24
    assert details['features']['ai_consultation']

def test_premium_tier_details():
    details = SubscriptionPricing.get_tier_details('premium')
    assert details['price'] == Decimal('99.99')
    assert details['ai_requests_per_hour'] == 500
    assert details['signal_changes'] == float('inf')
    assert details['signal_change_fee'] == Decimal('0.00')
    assert details['features']['custom_signals'] == float('inf')
    assert details['features']['portfolio_optimization']
    assert details['features']['one_on_one']

def test_invalid_tier_returns_free():
    details = SubscriptionPricing.get_tier_details('invalid')
    assert details == SubscriptionPricing.get_tier_details('free')

def test_signal_change_fees():
    assert SubscriptionPricing.calculate_signal_change_fee('free') == Decimal('3.00')
    assert SubscriptionPricing.calculate_signal_change_fee('pro') == Decimal('1.50')
    assert SubscriptionPricing.calculate_signal_change_fee('premium') == Decimal('0.00')

def test_ai_request_limits():
    assert SubscriptionPricing.get_ai_request_limit('free') == 10
    assert SubscriptionPricing.get_ai_request_limit('pro') == 100
    assert SubscriptionPricing.get_ai_request_limit('premium') == 500
