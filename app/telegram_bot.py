import os
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_test_message(chat_id: str, message: str = "Bot started!"):

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=chat_id, text=message)

if __name__ == "__main__":
    # Replace this with your actual Telegram user ID
    test_chat_id = "YOUR_TELEGRAM_USER_ID"
    send_test_message(test_chat_id)