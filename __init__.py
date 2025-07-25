import os
from flask import Flask


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        DEBUG=os.getenv('DEBUG', 'False') == 'True',
        TELEGRAM_BOT_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN'),
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

    # Register blueprints
    from web import app as web_app
    app.register_blueprint(web_app.bp)

    # Initialize database
    from app.models.models import create_tables
    create_tables()

    return app