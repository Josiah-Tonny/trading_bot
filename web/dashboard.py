import sys
import os

# Add the project root to Python path (same pattern as app.py)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Blueprint, render_template, session, redirect, url_for

# Direct import without try/except
from app.models.user import get_user_by_id

# Handle signals import gracefully
try:
    from app.signals.engine import generate_daily_signals
except ImportError:
    def generate_daily_signals(user):
        return []

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    print(f"=== DASHBOARD DEBUG ===")
    print(f"Session contents: {dict(session)}")
    
    user_id = session.get('user_id')
    print(f"user_id from session: {user_id}")
    
    if not user_id:
        print("❌ No user_id found - redirecting to login")
        return redirect('/login')
    
    # Use UserService instead of the convenience function
    from app.models.user import UserService
    try:
        with UserService() as service:
            user = service.get_user_by_id(user_id)
            print(f"User from database: {user}")
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return redirect('/login')
    
    if not user:
        print("❌ No user found in database - redirecting to login")
        return redirect('/login')
    
    print(f"✅ User found: {user}")
    
    signals = generate_daily_signals(user) if user else []
    print(f"✅ About to render dashboard template")
    
    return render_template('dashboard.html', user=user, signals=signals)

@dashboard_bp.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = get_user_by_id(user_id)
    return render_template('profile.html', user=user)
