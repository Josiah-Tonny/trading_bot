from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

PROVIDER_TOKEN: Optional[str] = os.getenv("PROVIDER_TOKEN")
if not PROVIDER_TOKEN:
    raise ValueError("PROVIDER_TOKEN environment variable not set.")

SYMBOL_CHANGE_PRICE: int = 100  # $1.00 in cents (USD)
CURRENCY: str = "USD"

async def change_symbol_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    prices = [LabeledPrice("Change Trading Symbol", SYMBOL_CHANGE_PRICE)]
    if update.message:
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
