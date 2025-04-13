from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, ConversationHandler, filters, ContextTypes, CallbackQueryHandler
from database import get_connection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Define conversation states
UPDATE_FIELD = range(1)

async def update_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Update a specific field in the application"""
    if not context.user_data.get('update_field'):
        await update.message.reply_text("Error: No field selected for update. Please try again.")
        return ConversationHandler.END
    
    field = context.user_data['update_field']
    new_value = update.message.text
    user_id = update.effective_user.id
    
    if new_value.lower() == "pending":
        new_value = None
    else:
        # For date fields, validate the date format
        if "date" in field or field in ["card_produced", "card_shipped", "card_delivered"]:
            try:
                # Validate the date format
                datetime.strptime(new_value, "%Y-%m-%d").date()
            except ValueError:
                await update.message.reply_text("Invalid format. Use YYYY-MM-DD or type 'pending'.")
                return UPDATE_FIELD
    
    # Map the callback data field to database column
    field_map = {
        "application_date": "application_date",
        "approval_date": "approval_date",
        "card_produced": "card_produced_date",
        "card_shipped": "card_shipped_date",
        "card_delivered": "card_delivered_date"
    }
    
    db_field = field_map.get(field)
    if not db_field:
        await update.message.reply_text(f"Error: Unknown field {field}.")
        return ConversationHandler.END
    
    # Update the database
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        f"UPDATE applications SET {db_field} = %s WHERE user_id = %s",
        (new_value, user_id)
    )
    
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"Your {field.replace('_', ' ')} has been updated. Use /track to see all applications."
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current operation"""
    await update.message.reply_text("Update cancelled.")
    return ConversationHandler.END

# Create the conversation handler for updating fields
update_field_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(
        lambda u, c: 1 if u.callback_query.data.startswith("update_") else None
    )],
    states={
        UPDATE_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_field)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)