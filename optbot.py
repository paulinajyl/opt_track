from telegram.ext import Application, CommandHandler, ConversationHandler
from handlers import start, track, clear, help
from add_new_opt_app_flow import conv_handler
from database import setup_database
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # this will be your fly.dev URL

def main():
    setup_database()
    print("📦 Database setup complete.")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start)) 
    app.add_handler(CommandHandler("help", help)) 
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("clear", clear))
    
    print("🤖 Bot is starting via webhook...")

    # Set webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=WEBHOOK_URL  # this will be something like https://opt-track.fly.dev
    )

if __name__ == "__main__":
    main()
