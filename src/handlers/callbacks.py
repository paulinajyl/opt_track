# In src/handlers/callbacks.py
from telegram import Update
from telegram.ext import ContextTypes
import logging
from handlers.command_handlers.track import track_handler
from handlers.command_handlers.update import update_handler, process_update_text
from handlers.conversation_handlers.add_new_opt_app_flow import add
from database import get_or_create_user, get_connection
from datetime import datetime

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
            
    elif query.data.startswith("update_"):
        # Handle update field selection
        field = query.data.replace("update_", "")
        
        # Handle premium processing toggle separately
        if field == "premium":
            await toggle_premium_processing(update, context)
        else:
            # For date fields, prompt for new value
            field_names = {
                "application_date": "application",
                "approval_date": "approval",
                "card_produced": "card produced",
                "card_shipped": "card shipped",
                "card_delivered": "card delivered"
            }
            
            # Store the field to update in context
            context.user_data['update_field'] = field
            
            await query.message.reply_text(
                f"Please enter the new {field_names.get(field, field)} date (YYYY-MM-DD) or type 'none' to clear this field:"
            )

async def toggle_premium_processing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle premium processing status"""
    user_id = update.effective_user.id
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current value
    cursor.execute(
        "SELECT premium_processing FROM applications WHERE user_id = %s",
        (user_id,)
    )
    result = cursor.fetchone()
    current_value = result[0] if result else None
    
    # Toggle value
    new_value = not current_value if current_value is not None else True
    
    # Update database
    cursor.execute(
        "UPDATE applications SET premium_processing = %s WHERE user_id = %s",
        (new_value, user_id)
    )
    conn.commit()
    conn.close()
    
    await update.callback_query.message.reply_text(
        f"Premium processing has been {'enabled' if new_value else 'disabled'} for your application."
    )