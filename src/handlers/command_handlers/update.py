# In src/handlers/command_handlers/update.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
import logging
from database import get_connection
from datetime import datetime

logger = logging.getLogger(__name__)

# This function can be imported in callbacks.py to handle text messages for field updates
async def process_update_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Process text input for updating fields"""
    if 'update_field' not in context.user_data:
        return False
    
    field = context.user_data['update_field']
    new_value = update.message.text
    
    # Database column names mapping
    db_field_names = {
        "application_date": "application_date",
        "approval_date": "approval_date",
        "card_produced": "card_produced_date",
        "card_shipped": "card_shipped_date",
        "card_delivered": "card_delivered_date"
    }
    
    db_field = db_field_names.get(field)
    
    if not db_field:
        await update.message.reply_text("Something went wrong. Please try again.")
        # Reset update field
        context.user_data.pop('update_field', None)
        return True
    
    # Handle clearing the field
    if new_value.lower() == 'none':
        new_value = None
    else:
        # Validate date format
        try:
            new_value = datetime.strptime(new_value, "%Y-%m-%d").date()
        except ValueError:
            await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD or type 'none'.")
            return True
    
    # Update database
    conn = get_connection()
    cursor = conn.cursor()
    
    update_query = f"UPDATE applications SET {db_field} = %s WHERE user_id = %s"

    cursor.execute(update_query, (new_value, update.effective_user.id))
    conn.commit()
    conn.close()
    
    readable_field = db_field.replace("_", " ").title()
    
    if new_value is None:
        await update.message.reply_text(f"{readable_field} has been cleared.")
    else:
        await update.message.reply_text(f"{readable_field} has been updated to {new_value}.")
    
    # Reset update field
    context.user_data.pop('update_field', None)
    
    return True  # Successfully handled update

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

# This can be added to main.py to handle text messages
async def update_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages for updating application fields"""
    # Try to process as an update text
    handled = await process_update_text(update, context)
    
    # If not handled as an update text, you could add other message handling here
    if not handled:
        pass  # Do nothing or handle other message types