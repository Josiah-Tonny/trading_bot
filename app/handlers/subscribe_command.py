from telegram import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# Replace with your actual Stripe provider token from BotFather
PROVIDER_TOKEN = "YOUR_STRIPE_PROVIDER_TOKEN"  # For Visa/Mastercard via Stripe

SUBSCRIPTION_PRICE = 1000  # $10.00 in cents (USD)
CURRENCY = "USD"

MPESA_NUMBER = "+254700000000"
PAYPAL_LINK = "https://www.paypal.me/yourbusiness"
BANK_DETAILS = "Bank: ABC Bank\nAccount: 123456789\nName: Your Name"

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Offer payment options: Telegram invoice (Visa), Mpesa, PayPal, Bank."""
    keyboard = [
        [InlineKeyboardButton("Pay with Card (Visa/Mastercard)", callback_data="pay_card")],
        [InlineKeyboardButton("Pay with Mpesa", callback_data="pay_mpesa")],
        [InlineKeyboardButton("Pay with PayPal", url=PAYPAL_LINK)],
        [InlineKeyboardButton("Direct Bank Deposit", callback_data="pay_bank")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Choose your payment method for subscription:",
        reply_markup=reply_markup
    )

async def subscribe_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection."""
    query = update.callback_query
    await query.answer()
    if query.data == "pay_card":
        prices = [LabeledPrice("Monthly Subscription", SUBSCRIPTION_PRICE)]
        await query.message.reply_invoice(
            title="Trading Bot Subscription",
            description="Access premium trading signals for 1 month.",
            payload="subscription_payload",
            provider_token=PROVIDER_TOKEN,
            currency=CURRENCY,
            prices=prices,
            need_name=True,
            need_email=True,
        )
    elif query.data == "pay_mpesa":
        await query.message.reply_text(
            f"Send payment via Mpesa to {MPESA_NUMBER}.\n"
            "After payment, send your transaction code here for manual verification."
        )
    elif query.data == "pay_bank":
        await query.message.reply_text(
            f"Deposit to:\n{BANK_DETAILS}\n"
            "After payment, send your transaction reference here for manual verification."
        )