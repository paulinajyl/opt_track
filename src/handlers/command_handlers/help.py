from telegram import Update,  InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging 

logger = logging.getLogger(__name__)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("👁️ See Applications", callback_data="show_track")],
        [InlineKeyboardButton("✏️ Add/Update Application", callback_data="show_add")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    help_message = (
        "A full list of the commands you can use:\n\n"
        "/add - start a new application.\n"
        "/track - show all existing applications.\n"
        "/cancel - stop an operation.\n"
        "/clear - clear your own application data from the bot.\n"
        "/help - show this help message again with available commands."
    )

    logger.info(f"User {update.effective_user.id} requested help")
    await update.message.reply_text(help_message, reply_markup=reply_markup)