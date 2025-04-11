from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import logging 

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} started the bot")
    await update.message.reply_text("hi let's consolidate all apps in one place! type /help")
