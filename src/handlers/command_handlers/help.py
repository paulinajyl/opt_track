from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import logging 

logger = logging.getLogger(__name__)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_message = (
        "here are the commands you can use:\n\n"
        "/add - write your name to start putting in your details.\n"
        "/cancel - stop inputting your details.\n"
        "/track - view all the tracked applications.\n"
        "/clear - clear your own application data from the bot.\n"
        "/help - show this help message again with available commands."
    )

    logger.info(f"User {update.effective_user.id} requested help")
    await update.message.reply_text(help_message)