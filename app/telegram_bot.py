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
import os
from dotenv import load_dotenv
from app.handlers.subscribe_command import subscribe_command, subscribe_callback_handler
from app.handlers.change_symbol import change_symbol_command
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


# /start command
async def start(update: Update, context: CallbackContext) -> None:
    if update.message:
        await update.message.reply_text("Welcome to crypto test")


# /help command
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


# Handle regular messages (e.g., payment codes)
async def message_handler(update: Update, context: CallbackContext) -> None:
    if update.message and update.message.text:
        text = update.message.text.strip()
        # Detect Mpesa code (e.g., "QW123ABC456")
        if re.match(r"^[A-Z0-9]{10,}$", text):
            # Store payment code securely in user_data
            context.user_data['pending_payment_code'] = text
            await update.message.reply_text("Thank you! Your payment code has been received and is under review.")
            # TODO: Add logic to verify and update subscription in DB
        else:
            await update.message.reply_text(f"You said: {text}")


# Error handler
async def error_handler(update: object, context: CallbackContext) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text('An error occurred. Please try again.')


async def subscribe(update: Update, context: CallbackContext) -> None:
    await subscribe_command(update, context)


async def status(update: Update, context: CallbackContext) -> None:
    if update.message:
        # Example: Retrieve subscription status from user_data
        status = context.user_data.get('subscription_status', 'inactive')
        await update.message.reply_text(
            f"Your subscription status: {status}."
        )


async def signals(update: Update, context: CallbackContext) -> None:
    if update.message:
        await update.message.reply_text(
            "Latest signals:\nEURUSD: BUY\nGBPUSD: SELL\n(More integration coming soon.)"
        )


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
            "Disclaimer: This is not financial advice. Use at your own risk. See full terms at [your link]."
        )


def main() -> None:
    if not TOKEN:
        logger.error("No token provided. Please set TELEGRAM_BOT_TOKEN environment variable.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

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

