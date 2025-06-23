# Tonny 

1. Basic Signal Engine Skeleton
Start implementing the core logic for fetching data and generating signals.
Begin with stubs in data_fetcher.py and engine.py. 

2. Telegram Bot Integration
Set up a basic Telegram bot using python-telegram-bot in telegram_bot.py.
Make sure you can send a test message to your Telegram account.

3. Configuration Management
Ensure sensitive info (like your Telegram token) is loaded from .env using python-dotenv.

4. Version Control & Collaboration
Make sure your .gitignore is set up to ignore sensitive and unnecessary files.
Push your initial setup to GitHub so collaborators can pull and contribute.

---

## Next Steps Tony

5. Signal Logic Implementation
- Implement technical indicators (EMA, MACD, RSI, ATR, etc.) in engine.py. ✅
- Add logic for multi-timeframe signals (5min, 15min, 4hr, 24hr). ✅
- Calculate TP/SL and trade amount per user risk profile/amount for each trade signal or amount to place for each trade. ✅

6. Telegram Bot & Web Integration
- Add user authentication: link Telegram user_id to web user account. ✅
- Implement /subscribe, /change_symbol, /status, /signals commands. ✅
- Integrate payment flow (Telegram Payments or Stripe/PayPal). ✅
- Set up webhook endpoints (Flask or FastAPI) for payment callbacks. ✅

7. Database Models
- Define models for users, subscriptions, signals, and trade logs in models.py.

---

# Felix

1. Web pages integration
    - base.html
    - index.html
    - signals.html
    - login.html
    - dashboard.html
2. User Authentication
    -Login and registration forms
    -User session management

---

## Next Steps Felix

3. User Registration & Login
- Build registration and login forms (templates/login.html, templates/register.html).
- Implement session management (Flask-Login or similar).
- After login, redirect users to dashboard.html with bot info and user-specific data.

4. Dashboard Integration
- Display user subscription status, recent signals, and trade stats.
- Add links/buttons to connect Telegram account (show Telegram user_id if available).

5. Link Bot & Web Templates
- Ensure users can log in via Telegram and access the web dashboard.
- On successful Telegram login, sync user session with web app.

---

# Integration Plan

- When a user logs in via Telegram, create or update their web user account.
- Use Telegram user_id as the primary key for linking bot and web sessions.
- After registration/login on the web, prompt users to connect their Telegram account for signal delivery.
- All trading signals, TP/SL, and trade info should be accessible both via Telegram and the web dashboard.

---

# Key Variables/Features to Implement

- User: id, telegram_user_id, email, password_hash, subscription_status, trial_start, trial_end
- Signal: id, symbol, timeframe, entry, tp, sl, risk, generated_at
- Subscription: user_id, tier, start_date, end_date, payment_status
- Payment: user_id, amount, type, status, timestamp
- Trade Log: user_id, signal_id, executed_at, result

---

# intergration

Telegram Bot: Payment & Subscription Flow
Implement /subscribe and /change_symbol commands in your Telegram bot (telegram_bot.py and handlers).
Integrate Telegram Payments API or Stripe/PayPal/mpesa/visa for subscriptions and symbol changes.
Handle payment callbacks: Set up webhook endpoints (Flask or FastAPI) to receive payment events and update user status in your database.

Files added:
    - app/handlers/subscribe_command.py
    - app/handlers/change_symbol.py

---

# Felix

1. Web pages integration
    - base.html
    - index.html
    - signals.html
    - login.html
    - dashboard.html
2. User Authentication
    -Login and registration forms
    -User session management