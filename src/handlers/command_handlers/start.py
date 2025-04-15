# In src/handlers/start.py
from telegram import Update
from telegram.ext import ContextTypes
import logging 

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} started the bot")
    
    await update.message.reply_text(
        "Hi! Let's consolidate all OPT applications in one place. Use /help for a complete list of commands.",
    )