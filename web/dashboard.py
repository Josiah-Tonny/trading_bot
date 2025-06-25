import sys
import os

# Add the project root to Python path (same pattern as app.py)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Blueprint, render_template, session, redirect, url_for

# Fix the import path
try:
    from app.models.user import get_user_by_id
except ImportError:
    # Fallback if the module doesn't exist
    def get_user_by_id(user_id):
        return None

# Handle signals import gracefully
try:
    from app.signals.engine import generate_daily_signals
except ImportError:
    # Placeholder function if signals module doesn't exist yet
    def generate_daily_signals(user):
        return []

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = get_user_by_id(user_id)
    signals = generate_daily_signals(user) if user else []
    return render_template('dashboard.html', user=user, signals=signals)

@dashboard_bp.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = get_user_by_id(user_id)
    return render_template('profile.html', user=user)
