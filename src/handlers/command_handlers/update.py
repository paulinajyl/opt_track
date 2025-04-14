# In src/handlers/command_handlers/update.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from database import get_connection

logger = logging.getLogger(__name__)

async def update_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /update command or update button callback"""
    logger.info(f"User {update.effective_user.id} requested update")
    
    # Check if this is from a callback query or direct command
    if update.callback_query:
        message_obj = update.callback_query.message
    else:
        message_obj = update.message
    
    user_id = update.effective_user.id
    
    # Check if user has an application
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE user_id = %s", (user_id,))
    application = cursor.fetchone()
    conn.close()
    
    if not application:
        await message_obj.reply_text(
            "You don't have any applications to update. Use /add to create one first."
        )
        return
    
    # Create update options keyboard
    keyboard = [
        [InlineKeyboardButton("Application Date", callback_data="update_application_date")],
        [InlineKeyboardButton("Approval Date", callback_data="update_approval_date")],
        [InlineKeyboardButton("Card Produced Date", callback_data="update_card_produced")],
        [InlineKeyboardButton("Card Shipped Date", callback_data="update_card_shipped")],
        [InlineKeyboardButton("Card Delivered Date", callback_data="update_card_delivered")],
        [InlineKeyboardButton("Premium Processing", callback_data="update_premium")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_obj.reply_text(
        "Select a field to update:",
        reply_markup=reply_markup
    )