# In src/handlers/callbacks.py - A simpler direct approach
from telegram import Update
from telegram.ext import ContextTypes
import logging
from handlers.command_handlers.track import track_handler
from handlers.command_handlers.start import start_handler
from handlers.command_handlers.update import update_handler
from handlers.conversation_handlers.add_new_opt_app_flow import add
from database import get_or_create_user, get_connection
from datetime import datetime

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline button callbacks"""
    query = update.callback_query
    logger.debug(f"Received callback query with data: {query.data}")
    
    await query.answer()  # Answer the callback query
    
    if query.data == "show_track":
        logger.debug("Handling show_track callback")
        await track_handler(update, context)
    elif query.data == "show_add":
        logger.debug("Handling show_add callback")
        if get_or_create_user(update.effective_user.id) is None:
            await query.message.reply_text( 
                f"No OPT application found for you. Please add your application using /add."
            )
        else:
            await update_handler(update, context)
    elif query.data.startswith("update_"):
        if query.data == "update_premium":
            await toggle_premium_processing(update, context)
        else:
            # For date fields, handle directly in this file
            await handle_field_update(update, context)

async def handle_field_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle updating a specific field directly"""
    query = update.callback_query
    field = query.data.replace("update_", "")
    
    field_names = {
        "application_date": "application",
        "approval_date": "approval",
        "card_produced": "card produced",
        "card_shipped": "card shipped",
        "card_delivered": "card delivered"
    }
    
    # Store the field to update in context for later
    context.user_data['update_field'] = field
    logger.debug(f"Stored field '{field}' in context.user_data")

    # Send prompt for input
    message = await query.message.reply_text(
        f"Please enter the new {field_names.get(field, field)} date (YYYY-MM-DD) or type 'pending' to clear this field:"
    )
    
    # Store the message ID to identify the response
    context.user_data['update_message_id'] = message.message_id

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("❗ message_handler triggered — conversation not active")
    """Handle text messages, including responses to field updates"""
    logger.debug("message_handler called")
    logger.debug(f"Context user data: {context.user_data}")
    
    # Check if we're expecting a field update
    if 'update_field' in context.user_data:
        logger.debug("Handling field update response")
        field = context.user_data['update_field']
        new_value = update.message.text
        user_id = update.effective_user.id
        
        logger.debug(f"Updating field: {field}")
        logger.debug(f"New value: {new_value}")
        
        if new_value.lower() == "none" or new_value.lower() == "pending":
            new_value = None
            await update.message.reply_text(
            f"Your {field.replace('_', ' ')} has been updated."
        )
        else:
            # For date fields, validate the date format
            if "date" in field or field in ["card_produced", "card_shipped", "card_delivered"]:
                try:
                    # Validate the date format
                    datetime.strptime(new_value, "%Y-%m-%d").date()
                except ValueError:
                    await update.message.reply_text("Invalid format. Use YYYY-MM-DD or type 'pending'.")
                    return
        
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
            return
        
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
            f"Your {field.replace('_', ' ')} has been updated."
        )
        
        # Clear the field from context
        del context.user_data['update_field']
        if 'update_message_id' in context.user_data:
            del context.user_data['update_message_id']

    else:
        # Handle other text messages here if needed
        logger.debug("Received text message but not in field update mode")

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