import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")
if TELEGRAM_CHAT_ID is None:
    raise ValueError("TELEGRAM_CHAT_ID is not set in the environment variables.")

async def send_test_message(chat_id: str, message: str = "Bot started!"):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message)

if __name__ == "__main__":
    asyncio.run(send_test_message(TELEGRAM_CHAT_ID))