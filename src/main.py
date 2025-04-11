from telegram.ext import Application
from add_new_opt_app_flow import conv_handler
from database import setup_database
import os
from dotenv import load_dotenv
import logging 

from handlers import command_handlers

load_dotenv()

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
WEBHOOK_URL = os.environ["WEBHOOK_URL"]


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    setup_database()
    print("📦 Database setup complete.")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    for h in command_handlers: 
        app.add_handler(h)

    app.add_handler(conv_handler)


    if os.environ['LOCAL_TEST_ENV'] == 'local':
        print("🤖 Bot is starting in polling mode (local development)...")
        app.run_polling()
        
    else:
        print("🤖 Bot is starting via webhook...")
        app.run_webhook(
            listen="0.0.0.0",
            port=8080,
            webhook_url=WEBHOOK_URL  # this will be something like https://opt-track.fly.dev
        )
        
if __name__ == "__main__":
    main()
