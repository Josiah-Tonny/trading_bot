from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes

PROVIDER_TOKEN = "YOUR_STRIPE_PROVIDER_TOKEN"
SYMBOL_CHANGE_PRICE = 100  # $1.00 in cents (USD)
CURRENCY = "USD"

async def change_symbol_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate Telegram payment for symbol change."""
    prices = [LabeledPrice("Change Trading Symbol", SYMBOL_CHANGE_PRICE)]
    await update.message.reply_invoice(
        title="Change Trading Symbol",
        description="Change or add a trading symbol to your subscription.",
        payload="change_symbol_payload",
        provider_token=PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=prices,
        need_name=True,
        need_email=True,
    )