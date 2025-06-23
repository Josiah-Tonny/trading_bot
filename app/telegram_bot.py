import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
    CallbackQueryHandler,
)
from telegram import Update
import logging
from dotenv import load_dotenv
from app.handlers.subscribe_command import subscribe_command, subscribe_callback_handler
from app.handlers.change_symbol import change_symbol_command
from app.signals.engine import generate_daily_signals
from app.models.user import get_user_by_telegram_id, create_user
from app.auth import authenticate
from app.payments import process_payment_code
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# --- User Authentication Integration ---
# When a user interacts with the bot, we link their Telegram user_id to a user account in our DB.
# If the user does not exist, we create a new user with their Telegram profile.
# This enables seamless linking between Telegram and web dashboard.

async def start(update: Update, context: CallbackContext) -> None:
    if update.message:
        telegram_profile = {
            "id": update.effective_user.id,
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name,
        }
        user = authenticate(telegram_profile=telegram_profile)
        await update.message.reply_text("Welcome to the trading bot! Your Telegram account is now linked.")

async def help_command(update: Update, context: CallbackContext) -> None:
    if update.message:
        await update.message.reply_text(
            "/start - Welcome message\n"
            "/help - Show this help message\n"
            "/subscribe - Start subscription/payment\n"
            "/status - Show your subscription status\n"
            "/signals - Get the latest trading signals\n"
            "/change_symbol - Change or add a trading symbol\n"
            "/support - Get support/contact info\n"
            "/terms - Show terms and disclaimer"
        )

# --- Payment Code Handler (Mpesa, Bank, etc.) ---
async def message_handler(update: Update, context: CallbackContext) -> None:
    if update.message and update.message.text:
        text = update.message.text.strip()
        # Detect payment code (e.g., Mpesa)
        if re.match(r"^[A-Z0-9]{10,}$", text):
            user_id = update.effective_user.id
            user = get_user_by_telegram_id(user_id)
            result = process_payment_code(user, text)
            if result["success"]:
                await update.message.reply_text("Payment received! Your subscription is now active.")
            else:
                await update.message.reply_text("Payment code invalid or already used. Please check and try again.")
        else:
            await update.message.reply_text(f"You said: {text}")

async def error_handler(update: object, context: CallbackContext) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text('An error occurred. Please try again.')

# --- Subscription Command ---
async def subscribe(update: Update, context: CallbackContext) -> None:
    await subscribe_command(update, context)

# --- Status Command ---
async def status(update: Update, context: CallbackContext) -> None:
    if update.message:
        user_id = update.effective_user.id
        user = get_user_by_telegram_id(user_id)
        if not user:
            await update.message.reply_text("No account found. Please /subscribe to start.")
            return
        status = "active" if user.is_active() else "inactive"
        expiry = user.subscription_expiry.strftime("%Y-%m-%d") if user.subscription_expiry else "N/A"
        await update.message.reply_text(
            f"Your subscription status: {status}.\nExpiry: {expiry}"
        )

# --- Signals Command ---
async def signals(update: Update, context: CallbackContext) -> None:
    if update.message:
        user_id = update.effective_user.id
        user = get_user_by_telegram_id(user_id)
        if not user or not user.is_active():
            await update.message.reply_text("You need an active subscription to receive signals.")
            return
        signals = generate_daily_signals(user)
        if not signals:
            await update.message.reply_text("No new signals at the moment. Please check back later.")
        else:
            for sig in signals:
                msg = (
                    f"Symbol: {sig['symbol']}\n"
                    f"Timeframe: {sig['timeframe']}\n"
                    f"Action: {sig['action'].upper()}\n"
                    f"Entry: {sig['entry']:.5f}\n"
                    f"TP: {', '.join([f'{tp:.5f}' for tp in sig['tp']])}\n"
                    f"SL: {sig['sl']:.5f}\n"
                    f"Confidence: {sig['confidence']}%\n"
                    f"Indicators: {sig['indicators']}\n"
                    f"Position Size: {sig.get('position_size', 0):.4f}"
                )
                await update.message.reply_text(msg)

# --- Change Symbol Command ---
async def change_symbol(update: Update, context: CallbackContext) -> None:
    await change_symbol_command(update, context)

async def support(update: Update, context: CallbackContext) -> None:
    if update.message:
        await update.message.reply_text(
            "For support, contact @YourSupportUsername or email support@example.com"
        )

async def terms(update: Update, context: CallbackContext) -> None:
    if update.message:
        await update.message.reply_text(
            "Disclaimer: This is not financial advice. Use at your own discretion. See full terms at [your link]."
        )

def main() -> None:
    if not TOKEN:
        logger.error("No token provided. Please set TELEGRAM_BOT_TOKEN environment variable.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # --- Command Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CallbackQueryHandler(subscribe_callback_handler, pattern="^pay_"))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("signals", signals))
    application.add_handler(CommandHandler("change_symbol", change_symbol))
    application.add_handler(CommandHandler("support", support))
    application.add_handler(CommandHandler("terms", terms))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error_handler)

    logger.info("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()

