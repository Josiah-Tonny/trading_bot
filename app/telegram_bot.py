import sys
import os
import logging
import re
from typing import Dict, Any, Optional, cast
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
    CallbackContext
)
from telegram.ext.filters import UpdateFilter
from dotenv import load_dotenv

# Local imports
from app.handlers.subscribe_command import subscribe_command, subscribe_callback_handler
from app.handlers.change_symbol import change_symbol_command
from app.signals.engine import generate_daily_signals
from app.models.user import UserOperations
from app.database import get_async_session
from app.auth.handlers import AuthHandler
from app.payments import process_payment_code

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

# Custom context type with proper typing
class ExtendedContext(ContextTypes.DEFAULT_TYPE):
    """Extended context type with proper user_data typing"""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._user_data: Dict[str, Any] = {}
    
    @property
    def user_data(self) -> Dict[str, Any]:
        return self._user_data
    
    @user_data.setter
    def user_data(self, value: Dict[str, Any]) -> None:
        self._user_data = value or {}

# --- Command Handlers ---

async def start(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle the /start command"""
    if not update.message or not update.effective_user:
        return
        
    telegram_id = update.effective_user.id
    async with get_async_session() as session:
        user_ops = UserOperations(session)
        
        # Check if user exists
        user = await user_ops.get_by_telegram_id(telegram_id)
        if user:
            await update.message.reply_text(
                "Welcome back! You can use /help to see available commands."
            )
        else:
            # Start registration process
            if not isinstance(context, ExtendedContext):
                context = cast(ExtendedContext, context)
            context.user_data['registration_step'] = 'email'
            await update.message.reply_text(
                "Welcome to Alpha Pro Trader! Let's set up your account.\n"
                "Please enter your email address:"
            )

async def handle_registration(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle user registration steps"""
    if not update.message or not update.message.text or not update.effective_user:
        return

    if not isinstance(context, ExtendedContext):
        context = cast(ExtendedContext, context)
        
    step = context.user_data.get('registration_step')
    text = update.message.text.strip()

    if step == 'email':
        if not re.match(r"[^@]+@[^@]+\.[^@]+", text):
            await update.message.reply_text("Please enter a valid email address.")
            return
        
        context.user_data['email'] = text
        context.user_data['registration_step'] = 'password'
        await update.message.reply_text(
            "Great! Now please enter a password (minimum 8 characters):"
        )
    
    elif step == 'password':
        if len(text) < 8:
            await update.message.reply_text("Password must be at least 8 characters long.")
            return
        
        # Register user
        auth_data = {
            'email': context.user_data['email'],
            'password': text,
            'telegram_id': update.effective_user.id
        }
        
        async with get_async_session() as session:
            auth_handler = AuthHandler(session)
            result = await auth_handler.register_user(auth_data)
            
            if result.success:
                context.user_data.clear()
                await update.message.reply_text(
                    "Registration successful! You can now use all bot features.\n"
                    "Use /help to see available commands."
                )
            else:
                await update.message.reply_text(
                    f"Registration failed: {result.message}\n"
                    "Please try again with /start"
                )

async def help_command(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle the /help command"""
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/subscribe - Subscribe to signals
/status - Check your subscription status
/signals - Get latest trading signals
/support - Contact support
/terms - View terms of service
    """
    if update.message:
        await update.message.reply_text(help_text.strip())

# --- Payment Code Handler ---

async def message_handler(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle incoming messages for payment codes"""
    if not update.message or not update.message.text or not update.effective_user:
        return
        
    text = update.message.text.strip()
    if len(text) < 5:  # Basic validation for payment codes
        return
        
    async with get_async_session() as session:
        user_ops = UserOperations(session)
        user = await user_ops.get_by_telegram_id(update.effective_user.id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
            
        result = await process_payment_code(user, text)
        await update.message.reply_text(result.get('message', 'Payment processed'))

# --- Error Handler ---

async def error_handler(update: object, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Log errors and handle them gracefully"""
    logger.error("Error while processing update:", exc_info=context.error)
    if update and isinstance(update, Update) and update.message:
        await update.message.reply_text("An error occurred. Please try again later.")

# --- Subscription Command ---

async def subscribe(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle subscription command"""
    await subscribe_command(update, context)

# --- Status Command ---

async def status(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle status command"""
    if not update.effective_user:
        return
        
    async with get_async_session() as session:
        user_ops = UserOperations(session)
        user = await user_ops.get_by_telegram_id(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
            
        status_text = "Active" if user.is_active else "Inactive"
        expiry = user.subscription_expiry.strftime("%Y-%m-%d %H:%M:%S") if user.subscription_expiry else "N/A"
        
        await update.message.reply_text(
            f"Subscription Status: {status_text}\n"
            f"Expiry Date: {expiry}"
        )

# --- Signals Command ---

async def signals(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle signals command"""
    if not update.effective_user:
        return
        
    async with get_async_session() as session:
        user_ops = UserOperations(session)
        user = await user_ops.get_by_telegram_id(update.effective_user.id)
        
        if not user or not user.is_active:
            await update.message.reply_text(
                "You need an active subscription to receive signals.\n"
                "Use /subscribe to get started."
            )
            return
            
        signals = await generate_daily_signals()
        if signals:
            response = "\n".join(
                f"{s['symbol']}: {s['signal']} - {s['confidence']}%"
                for s in signals
            )
        else:
            response = "No signals available at the moment."
            
        await update.message.reply_text(f"Latest Signals:\n{response}")

# --- Change Symbol Command ---

async def change_symbol(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle symbol change command"""
    await change_symbol_command(update, context)

# --- Support Command ---

async def support(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle support command"""
    if update.message:
        await update.message.reply_text(
            "For support, please contact us at support@tradingbot.com\n"
            "We typically respond within 24 hours."
        )

# --- Terms Command ---

async def terms(update: Update, context: CallbackContext[object, dict, Any, Any]) -> None:
    """Handle terms command"""
    if update.message:
        await update.message.reply_text(
            "Terms of Service:\n"
            "1. This is a demo trading bot.\n"
            "2. Use at your own risk.\n"
            "3. No financial advice is provided."
        )

def main() -> None:
    """Start the bot"""
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder()\
        .token(TOKEN)\
        .context_types(ContextTypes(context=ExtendedContext))\
        .build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("signals", signals))
    application.add_handler(CommandHandler("support", support))
    application.add_handler(CommandHandler("terms", terms))
    
    # Add message handler for payment codes
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()
