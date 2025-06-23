# Trading Bot Project

This project includes:
- A Flask web application
- A Telegram bot for trading signals and subscriptions

## Setup

1. **Clone the repository** (if not already done):

   ```sh
   git clone <your-repo-url>
   cd trading_bot
   ```

2. **Create and activate a virtual environment:**

   ```sh
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Environment Variables:**

   - Copy `.env.example` to `.env` and set your environment variables, especially `TELEGRAM_BOT_TOKEN` for the Telegram bot.

## Running the Flask Web App

1. **Set environment variables if needed** (e.g., `FLASK_APP`):

   ```sh
   set FLASK_APP=web/app.py
   set FLASK_ENV=development
   ```

   Or on Unix/Mac:

   ```sh
   export FLASK_APP=web/app.py
   export FLASK_ENV=development
   ```

2. **Run the Flask app:**

   ```sh
   flask run
   ```

   The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Running the Telegram Bot

1. **Ensure your `.env` file contains `TELEGRAM_BOT_TOKEN`.**

2. **Run the bot:**

   ```sh
   python app/telegram_bot.py
   ```

   The bot will start polling for messages.

## Notes

- Make sure your database (if used) is set up and configured in your environment variables or config files.
- For production deployments, use a production-ready WSGI server (e.g., Gunicorn) and secure your environment variables.

## Troubleshooting

- If you encounter issues with missing packages, ensure your virtual environment is activated and all dependencies are installed.
- For Telegram bot issues, verify your bot token and network connectivity.