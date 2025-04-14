# In src/handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging 

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} started the bot")
    
    keyboard = [
        [InlineKeyboardButton("👁️ See Applications", callback_data="show_track")],
        [InlineKeyboardButton("✏️ Add/Update Application", callback_data="show_add")]
    ]
    
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Hi! Let's consolidate all OPT applications in one place. What would you like to do?",
        reply_markup=reply_markup
    )