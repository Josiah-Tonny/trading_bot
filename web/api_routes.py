from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.services.subscription_service import SubscriptionService
from app.services.signal_management import SignalManagementService
from app.services.ai_consultation import AIConsultationService
from app.models.models import SessionLocal
import json

api = Blueprint('api', __name__)

@api.route('/api/subscription/status')
@login_required
def get_subscription_status():
    """Get current user's subscription status"""
    db = SessionLocal()
    try:
        subscription_service = SubscriptionService(db)
        status = subscription_service.get_subscription_details(current_user.id)
        return jsonify(status)
    finally:
        db.close()

@api.route('/api/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    """Upgrade user's subscription tier"""
    data = request.get_json()
    new_tier = data.get('tier')
    payment_method = data.get('payment_method')
    
    if not new_tier or not payment_method:
        return jsonify({'error': 'Missing required parameters'}), 400
        
    db = SessionLocal()
    try:
        subscription_service = SubscriptionService(db)
        result = subscription_service.upgrade_subscription(
            current_user.id,
            new_tier,
            payment_method
        )
        return jsonify(result)
    finally:
        db.close()

@api.route('/api/signals/available')
@login_required
def get_available_signals():
    """Get user's available signals"""
    db = SessionLocal()
    try:
        signal_service = SignalManagementService(db)
        signals = signal_service.get_available_signals(current_user.id)
        return jsonify(signals)
    finally:
        db.close()

@api.route('/api/signals/change', methods=['POST'])
@login_required
def change_signal():
    """Change a trading signal"""
    data = request.get_json()
    new_symbol = data.get('newSymbol')
    payment_method = data.get('paymentMethod')
    
    if not new_symbol:
        return jsonify({'error': 'New symbol is required'}), 400
        
    db = SessionLocal()
    try:
        signal_service = SignalManagementService(db)
        result = signal_service.change_signal(
            current_user.id,
            new_symbol,
            payment_method
        )
        return jsonify(result)
    finally:
        db.close()

@api.route('/api/ai/advice', methods=['POST'])
@login_required
def get_ai_advice():
    """Get AI trading advice"""
    data = request.get_json()
    symbol = data.get('symbol')
    timeframe = data.get('timeframe')
    
    if not symbol or not timeframe:
        return jsonify({'error': 'Symbol and timeframe are required'}), 400
        
    db = SessionLocal()
    try:
        # Get user's active subscription
        subscription_service = SubscriptionService(db)
        subscription = subscription_service.get_active_subscription(current_user.id)
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 403
            
        # Get market data
        from app.data_fetcher import fetch_ohlc_data
        market_data = fetch_ohlc_data(symbol, timeframe)
        
        # Get AI advice
        ai_service = AIConsultationService(db)
        advice = ai_service.get_trading_advice(
            current_user,
            subscription,
            market_data
        )
        
        return jsonify(advice)
    finally:
        db.close()

@api.route('/api/ai/features')
@login_required
def get_ai_features():
    """Get available AI features for current subscription"""
    db = SessionLocal()
    try:
        subscription_service = SubscriptionService(db)
        subscription = subscription_service.get_active_subscription(current_user.id)
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 403
            
        ai_service = AIConsultationService(db)
        features = ai_service.get_available_features(subscription)
        
        return jsonify(features)
    finally:
        db.close()

@api.route('/api/subscription/trial/setup', methods=['POST'])
@login_required
def setup_trial_access():
    """Set up trial access hours for free tier"""
    data = request.get_json()
    access_hours = data.get('accessHours')  # Format: "HH:MM-HH:MM"
    
    if not access_hours:
        return jsonify({'error': 'Access hours are required'}), 400
        
    db = SessionLocal()
    try:
        subscription_service = SubscriptionService(db)
        result = subscription_service.set_trial_access_hours(
            current_user.id,
            access_hours
        )
        return jsonify(result)
    finally:
        db.close()

@api.route('/api/subscription/check-access')
@login_required
def check_access():
    """Check if user has access during their selected hours (free tier)"""
    db = SessionLocal()
    try:
        subscription_service = SubscriptionService(db)
        access = subscription_service.check_access(current_user.id)
        return jsonify(access)
    finally:
        db.close()

# Error handlers
@api.errorhandler(Exception)
def handle_error(error):
    current_app.logger.error(f"API Error: {str(error)}")
    return jsonify({
        'error': 'An unexpected error occurred',
        'message': str(error)
    }), 500
