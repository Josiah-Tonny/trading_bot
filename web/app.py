import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from typing import Callable, TypeVar, Any
from flask import Response

load_dotenv()  # Load environment variables from .env

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Add this context processor for global template access
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
    return decorated_function  # type: ignore

@app.route('/')
def index():
    return render_template('index.html', user_authenticated='user' in session)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # TODO: Replace with real DB/Telegram bot check
        if email == 'demo@tradepro.com' and password == 'demo123':
            session['user'] = email
            # TODO: Optionally notify/sync with Telegram bot here
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # TODO: Save user to DB and/or notify Telegram bot
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/signals')
@login_required
def signals():
    return render_template('signals.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

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
    return render_template('support.html')  # Create this template

@app.route('/terms')
def terms():
    return render_template('terms.html')  # Create this template

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')  # Create this template

# Placeholder for Stripe webhook endpoint
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    # TODO: Validate and process Stripe webhook events
    return '', 200

# Placeholder for signal API endpoint
@app.route('/api/signal', methods=['POST'])
def api_signal():
    # TODO: Authenticate and deliver trading signals
    return jsonify({'status': 'ok', 'message': 'Signal endpoint placeholder'})

@app.route('/api/message', methods=['POST'])
def api_message():
    data = request.json
    # Process the incoming message
    message = data.get('message') if data else ''
    response = {"reply": f"You said: {message}"}
    return jsonify(response)

# Example API endpoint for Telegram bot sync (optional)
@app.route('/api/sync_user', methods=['POST'])
def sync_user():
    data = request.json
    # TODO: Sync user info with Telegram bot or DB
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)