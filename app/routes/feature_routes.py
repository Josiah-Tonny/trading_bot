from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.services.education_service import EducationService
from app.services.signal_generation_service import SignalGenerationService
from app.services.usage_tracking_service import UsageTrackingService
from app.models.models import SessionLocal

api_features = Blueprint('api_features', __name__)

@api_features.route('/api/education/content')
@login_required
async def get_educational_content():
    """Get educational content based on subscription level"""
    db = SessionLocal()
    try:
        education_service = EducationService(db)
        usage_service = UsageTrackingService(db)
        
        # Track usage
        if not await usage_service.track_usage(current_user, 'educational_access'):
            return jsonify({'error': 'Usage limit reached'}), 429
            
        content = await education_service.get_educational_content(current_user)
        return jsonify(content)
    finally:
        db.close()

@api_features.route('/api/signals/generate')
@login_required
async def generate_signals():
    """Generate trading signals based on subscription tier"""
    db = SessionLocal()
    try:
        signal_service = SignalGenerationService(db)
        usage_service = UsageTrackingService(db)
        
        # Track usage
        if not await usage_service.track_usage(current_user, 'signal_requests'):
            return jsonify({'error': 'Signal generation limit reached'}), 429
            
        signals = await signal_service.get_signals(current_user)
        return jsonify(signals)
    finally:
        db.close()

@api_features.route('/api/signals/analytics/<signal_id>')
@login_required
async def get_signal_analytics(signal_id):
    """Get detailed signal analytics (Premium feature)"""
    db = SessionLocal()
    try:
        signal_service = SignalGenerationService(db)
        usage_service = UsageTrackingService(db)
        
        # Track usage
        if not await usage_service.track_usage(current_user, 'ai_consultations'):
            return jsonify({'error': 'AI consultation limit reached'}), 429
            
        signal = {'id': signal_id}  # Get actual signal from database
        analytics = await signal_service.get_signal_analytics(current_user, signal)
        return jsonify(analytics)
    finally:
        db.close()

@api_features.route('/api/signals/validate', methods=['POST'])
@login_required
async def validate_signal():
    """Validate custom trading signal (Pro/Premium feature)"""
    data = request.get_json()
    db = SessionLocal()
    try:
        signal_service = SignalGenerationService(db)
        usage_service = UsageTrackingService(db)
        
        # Track usage
        if not await usage_service.track_usage(current_user, 'custom_signals'):
            return jsonify({'error': 'Custom signal limit reached'}), 429
            
        validation = await signal_service.validate_signal(current_user, data)
        return jsonify(validation)
    finally:
        db.close()
