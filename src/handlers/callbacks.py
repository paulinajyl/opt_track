# In src/handlers/callbacks.py
from telegram import Update
from telegram.ext import ContextTypes
import logging

from handlers.track import track_handler  

logger = logging.getLogger(__name__)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline button callbacks"""
    query = update.callback_query
    await query.answer()  # Answer the callback query
    
    if query.data == "show_track":
        # Call the track handler
        await track_handler(update, context)
        
    elif query.data == "show_add":
        # Tell user to use the /add command
        await query.message.reply_text("To add an application, please use the /add command.")