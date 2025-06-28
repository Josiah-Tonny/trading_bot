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
- Implement technical indicators (EMA, MACD, RSI, ATR, etc.) in engine.py. 
- Add logic for multi-timeframe signals (5min, 15min, 4hr, 24hr). 
- Calculate TP/SL and trade amount per user risk profile/amount for each trade signal or amount to place for each trade. 

6. Telegram Bot & Web Integration
- Add user authentication: link Telegram user_id to web user account. 
- Implement /subscribe, /change_symbol, /status, /signals commands. 
- Integrate payment flow (Telegram Payments or Stripe/PayPal). 
- Set up webhook endpoints (Flask or FastAPI) for payment callbacks. 

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

## TONNY Signal Engine Enhancements

### Technical Indicators Implementation

1. **Moving Averages**
   - Simple Moving Average (SMA): 
     ```python
     SMA = sum(Close[i-n:i]) / n
     ```
   - Exponential Moving Average (EMA):
     ```python
     EMA = (Close[i] * (2/(1+n))) + (EMA[i-1] * (1-(2/(1+n))))
     ```
   
2. **Trend Indicators**
   - **ADX (Average Directional Index)**:
     ```python
     +DI = 100 * (Smoothed +DM / True Range)
     -DI = 100 * (Smoothed -DM / True Range)
     DX = 100 * (|+DI - -DI| / (+DI + -DI))
     ADX = (Prior ADX * (n-1) + Current DX) / n
     ```
     - ADX > 40: Strong trend
     - ADX 25-40: Moderate trend
     - ADX < 25: Weak trend
   
3. **Momentum Indicators**
   - **RSI (Relative Strength Index)**:
     ```python
     RS = Average Gain / Average Loss
     RSI = 100 - (100 / (1 + RS))
     ```
     - RSI > 70: Overbought
     - RSI < 30: Oversold
     - RSI 30-70: Neutral
   
   - **Stochastic Oscillator**:
     ```python
     %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
     %D = 3-day SMA of %K
     ```
     - %K > 80: Strong buying pressure
     - %K < 20: Strong selling pressure
     - %K 20-80: Balanced market
   
4. **Volatility Indicators**
   - **Standard Deviation**:
     ```python
     σ = sqrt(sum((x - μ)^2) / n)
     ```
     - σ > 1.5 * avg_σ: High volatility
     - σ < 0.8 * avg_σ: Low volatility
     - Normal volatility: 0.8 * avg_σ < σ < 1.5 * avg_σ
   
   - **Bollinger Bands**:
     ```python
     Upper Band = SMA + (σ * 2)
     Lower Band = SMA - (σ * 2)
     ```
   
5. **Volume Indicators**
   - **VWAP (Volume Weighted Average Price)**:
     ```python
     VWAP = sum(Typical Price * Volume) / sum(Volume)
     ```
   - **VWMA (Volume Weighted Moving Average)**:
     ```python
     VWMA = sum(Close * Volume) / sum(Volume)
     ```

### Signal Generation Logic

1. **Trade Duration Calculation**
   ```python
   Base Durations:
   - 5m: 5-15 minutes
   - 15m: 15-45 minutes
   - 4h: 4-12 hours
   - 1d: 1-2 days
   
   Adjustments:
   - High volatility: Reduce duration
   - Strong trend: Extend duration
   - Weak trend: Reduce duration
   ```

2. **Market Condition Analysis**
   ```python
   Conditions:
   - Trend: ADX > 40 (Strong), 25-40 (Moderate), <25 (Weak)
   - Momentum: RSI > 70 (Overbought), <30 (Oversold)
   - Volatility: σ > 1.5 * avg_σ (High), <0.8 * avg_σ (Low)
   - Market Pressure: %K > 80 (Strong Buying), <20 (Strong Selling)
   ```

3. **Signal Confidence Scoring**
   ```python
   Confidence Factors:
   - RSI confirmation: 10 points
   - Stochastic confirmation: 10 points
   - ADX strength: 10 points
   - Price above/below EMA: 10 points
   - MACD confirmation: 10 points
   - Volume confirmation: 10 points
   
   Max Confidence: 100%
   ```

4. **Risk Management**
   ```python
   Take Profit Levels:
   - Short-term (5m, 15m): 1x, 1.5x, 2x ATR
   - Medium-term (4h): 2x, 3x, 4x ATR
   - Long-term (1d): 3x, 4x, 5x ATR
   
   Stop Loss:
   - Short-term: 1x ATR
   - Medium-term: 1.2x-1.5x ATR
   - Long-term: 2x ATR
   ```

### Usage Examples

1. **Generating Signals**
   ```python
   signal_engine = SignalEngine(data, timeframe="15m")
   signal = signal_engine.generate_signal(capital=1000)
   ```

2. **Getting Market Conditions**
   ```python
   conditions = signal_engine._get_market_conditions()
   # Returns: "Strong uptrend, Overbought, Normal volatility, Balanced market"
   ```

3. **Trade Duration**
   ```python
   duration = signal_engine._get_trade_duration()
   # Returns: "15-45 minutes (Low volatility, strong trend - good conditions)"
   ```

4. **Trade Explanation**
   ```python
   explanation = signal_engine._explain_trade('buy', rsi=35, stoch_k=25, adx=45)
   # Returns: "BUY signal generated. Strong trend confirmation - ADX above 40. Neutral to bullish momentum. Moderate buy signal from Stochastic Oscillator. Confidence Level: 70%"
   ```

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