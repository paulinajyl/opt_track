from telegram.ext import Application, CommandHandler, ConversationHandler
from handlers import add, track, clear, cancel, help
from chatwithuser import conv_handler
from database import setup_database
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']

def main():
    setup_database()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("help", help)) 

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("clear", clear))
    
    app.run_polling()

if __name__ == "__main__":
    main()
