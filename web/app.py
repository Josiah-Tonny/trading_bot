import os
import sys
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from typing import Callable, TypeVar, Any

# Load environment variables first
load_dotenv()

# Generate secure secret key if not provided
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    print("⚠️  WARNING: Generated temporary secret key.")

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Initialize Flask app FIRST
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Explicit session configuration to fix cookie issues
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_PATH='/',
    SESSION_COOKIE_DOMAIN=None,
    PERMANENT_SESSION_LIFETIME=3600,
    SESSION_REFRESH_EACH_REQUEST=True
)

print("✅ Using cookie-based sessions with explicit config")

# Database initialization
try:
    from app.models.models import create_tables
    print("Initializing database...")
    create_tables()
    
    try:
        from app.models.user import UserService
        with UserService() as service:
            existing_user = service.get_user_by_email("test@example.com")
            if not existing_user:
                user = service.create_user(
                    email="test@example.com",
                    password="password123"
                )
                print(f"✅ Created sample user: {user.email}")
                print("   Login with: test@example.com / password123")
            else:
                print("✅ Sample user already exists")
    except Exception as e:
        print(f"Note: Could not create sample user: {e}")
        
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")

# Import other modules
from app.auth import authenticate
from app.models.user import get_user_by_email, create_user, get_user_by_telegram_id
import app.models.models as User

# Handle payment imports gracefully
try:
    from app.payments import process_stripe_webhook, process_paypal_webhook
except ImportError:
    def process_stripe_webhook(payload, sig_header):
        return None
    def process_paypal_webhook(data):
        return None

# Import and register blueprint AFTER app is fully configured
from web.dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)

@app.context_processor
def inject_user():
    return dict(user_authenticated='user' in session)

F = TypeVar("F", bound=Callable[..., Any])

def login_required(f: F) -> F:
    from functools import wraps
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html', user_authenticated='user' in session, username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"LOGIN DEBUG - Secret key exists: {bool(app.secret_key)}")
        print(f"LOGIN DEBUG - Cookie config: {app.config.get('SESSION_COOKIE_PATH')}")
        
        from app.models.user import UserService
        with UserService() as service:
            user = service.authenticate_user(email, password)
            
        if user:
            print(f"LOGIN DEBUG - User authenticated: {user.id}")
            
            # Clear session completely
            session.clear()
            
            # Set session data
            session['user'] = user.email or str(user.telegram_user_id)
            session['user_id'] = user.id
            session.permanent = True
            
            # Force session to be marked as modified
            session.modified = True
            
            print(f"LOGIN DEBUG - Session after setting: {dict(session)}")
            print(f"LOGIN DEBUG - Session permanent: {session.permanent}")
            print(f"LOGIN DEBUG - Session modified: {session.modified}")
            
            # Create response with explicit redirect
            response = redirect('/dashboard')
            
            # Ensure session cookie is set properly
            print(f"LOGIN DEBUG - Response headers will include session cookie")
            
            return response
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Test routes for debugging
@app.route('/test-session-set')
def test_session_set():
    session.clear()
    session['test_key'] = 'test_value'
    session['user_id'] = 999
    session.permanent = True
    session.modified = True
    return f"Session set: {dict(session)}"

@app.route('/test-session-get')
def test_session_get():
    return f"Session contents: {dict(session)}"

@app.route('/test-direct-dashboard')
def test_direct_dashboard():
    """Test dashboard access without blueprint"""
    print(f"DIRECT DASHBOARD TEST - Session: {dict(session)}")
    user_id = session.get('user_id')
    if not user_id:
        return "No user_id in session"
    
    from app.models.user import UserService
    try:
        with UserService() as service:
            user = service.get_user_by_id(user_id)
            return f"User found: {user.email if user else 'None'}"
    except Exception as e:
        return f"Error: {e}"

# Password reset functions
def forgot_password(email):
    from app.models.user import UserService
    try:
        with UserService() as service:
            user = service.get_user_by_email(email)
            if user:
                token = secrets.token_urlsafe(32)
                session[f'reset_token_{token}'] = {'email': email, 'expires': 3600}
                return token
    except Exception as e:
        print(f"Password reset error: {e}")
    return None

def perform_password_reset(token, new_password):
    token_key = f'reset_token_{token}'
    if token_key in session:
        email = session[token_key]['email']
        from app.models.user import UserService
        try:
            with UserService() as service:
                user = service.get_user_by_email(email)
                if user:
                    session.pop(token_key, None)
                    return True
        except Exception as e:
            print(f"Password reset error: {e}")
    return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_route():
    if request.method == 'POST':
        email = request.form.get('email')
        token = forgot_password(email)
        if token:
            flash(f"Password reset link sent to {email}. (Token: {token})", "info")
        else:
            flash("Email not found.", "danger")
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_route(token):
    if request.method == 'POST':
        new_password = request.form.get('password')
        if perform_password_reset(token, new_password):
            flash("Password reset successful. Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid or expired token.", "danger")
    return render_template('reset_password.html', token=token)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone_number = request.form.get('phone_number')
        username = request.form.get('username')
        try:
            user = create_user(email=email, password=password, first_name=first_name,
                               last_name=last_name, phone_number=phone_number, username=username)
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/signals')
@login_required
def signals():
    return render_template('signals.html')

@app.route('/portfolio')
@login_required
def portfolio():
    return render_template('portfolio.html')

@app.route('/trade')
@login_required
def trade():
    return render_template('trade.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# API endpoints
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    event = process_stripe_webhook(payload, sig_header)
    if event and event['type'] == 'checkout.session.completed':
        telegram_user_id = event['data']['object']['metadata']['telegram_user_id']
        user = get_user_by_telegram_id(telegram_user_id)
        if user:
            user.subscription_status = 'active'
    return jsonify(success=True)

@app.route('/webhook/paypal', methods=['POST'])
def paypal_webhook():
    data = request.json
    event = process_paypal_webhook(data)
    if event and event['event_type'] == 'PAYMENT.SALE.COMPLETED':
        telegram_user_id = event['resource']['custom']
        user = get_user_by_telegram_id(telegram_user_id)
        if user:
            user.subscription_status = 'active'
    return jsonify(success=True)

@app.route('/api/signal', methods=['POST'])
def api_signal():
    return jsonify({'status': 'ok', 'message': 'Signal endpoint placeholder'})

@app.route('/api/message', methods=['POST'])
def api_message():
    data = request.json
    message = data.get('message') if data else ''
    response = {"reply": f"You said: {message}"}
    return jsonify(response)

@app.route('/api/sync_user', methods=['POST'])
def sync_user():
    data = request.json
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)