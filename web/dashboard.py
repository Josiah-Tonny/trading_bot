from flask import Blueprint, render_template, session, redirect, url_for
from app.models.user import get_user_by_id  # to be implemented
from app.signals.engine import generate_daily_signals

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