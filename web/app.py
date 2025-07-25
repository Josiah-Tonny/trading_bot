import os
import sys
import secrets
from flask import Flask, Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from dotenv import load_dotenv
from typing import Callable, TypeVar, Any, Optional

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

# Create a Blueprint for the web routes
bp = Blueprint('web', __name__)

# Import database models and services after app is created to avoid circular imports
def get_user_service():
    from app.models.user import UserService
    return UserService()

# Routes
@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with get_user_service() as service:
            user = service.authenticate_user(email, password)
            if user:
                session['user_id'] = str(user.id)
                session.permanent = True
                flash('Login successful!', 'success')
                return redirect(url_for('web.dashboard'))
            
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with get_user_service() as service:
            if service.get_user_by_email(email):
                flash('Email already registered', 'error')
            else:
                user = service.create_user(email, password)
                if user:
                    flash('Registration successful! Please log in.', 'success')
                    return redirect(url_for('web.login'))
                
        flash('Registration failed', 'error')
    
    return render_template('register.html')

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    with get_user_service() as service:
        user = service.get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('web.login'))
    
    return render_template('dashboard.html', user=user)

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('web.index'))

# Error handlers
@bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Favicon route
@bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('favicon.ico')

# Context processor to make variables available to all templates
@bp.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        with get_user_service() as service:
            user = service.get_user_by_id(session['user_id'])
    return dict(current_user=user)

# Type variables for decorators
F = TypeVar('F', bound=Callable[..., Any])

def login_required(f: F) -> F:
    """Decorator to ensure a user is logged in."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('web.login', next=request.url))
        return f(*args, **kwargs)
    
    return decorated_function  # type: ignore

# Create the Flask app
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Register blueprints
    app.register_blueprint(bp)
    
    # Ensure the static folder is properly configured
    app.static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    
    # Configure template auto-reload in development
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Initialize extensions
    from app.extensions import db
    db.init_app(app)
    
    # Register error handlers
    app.register_error_handler(404, not_found_error)
    app.register_error_handler(500, internal_error)
    
    # Add context processor
    app.context_processor(inject_user)
    
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)