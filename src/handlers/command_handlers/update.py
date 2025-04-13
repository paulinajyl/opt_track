# In src/handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging 

logger = logging.getLogger(__name__)

async def update_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Application Date", callback_data="update_application_date")],
        [InlineKeyboardButton("Approval Date", callback_data="update_approval_date")],
        [InlineKeyboardButton("Card Produced Date", callback_data="update_card_produced")],
        [InlineKeyboardButton("Card Shipped Date", callback_data="update_card_shipped")],
        [InlineKeyboardButton("Card Delivered Date", callback_data="update_card_delivered")],
        [InlineKeyboardButton("Add Premium Processing", callback_data="update_premium")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.reply_text(
        "We found an existing application. Select a field to update:",
        reply_markup=reply_markup
    )