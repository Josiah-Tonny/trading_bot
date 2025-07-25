import os
from flask import Flask


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        DEBUG=os.getenv('DEBUG', 'False') == 'True',
        TELEGRAM_BOT_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN'),
        # Database configuration
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(app.instance_path, 'trading_bot.db')),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Session configuration
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_PATH='/',
        PERMANENT_SESSION_LIFETIME=3600,
        SESSION_REFRESH_EACH_REQUEST=True
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.update(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    from .app.extensions import db, login_manager, migrate
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .web.app import bp as web_bp
    app.register_blueprint(web_bp, url_prefix='/')

    # Import models for SQLAlchemy
    from .app import models  # This ensures models are registered with SQLAlchemy
    
    # Create database tables
    with app.app_context():
        db.create_all()

    return app