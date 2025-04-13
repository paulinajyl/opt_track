# In src/handlers/callbacks.py
from telegram import Update
from telegram.ext import ContextTypes
import logging

from handlers.command_handlers.track import track_handler
from handlers.command_handlers.update import update_handler  
from handlers.conversation_handlers.add_new_opt_app_flow import add 

from database import get_or_create_user

logger = logging.getLogger(__name__)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline button callbacks"""
    query = update.callback_query
    await query.answer()  # Answer the callback query
    
    if query.data == "show_track":
        # Call the track handler
        await track_handler(update, context)
        
    elif query.data == "show_add":
        if get_or_create_user(update.effective_user.id) is None:
            await add(update, context)
        
        else: 
            await update_handler(update, context)