# In src/handlers/track.py
from telegram import Update
from telegram.ext import ContextTypes
import logging
from database import get_connection
logger = logging.getLogger(__name__)

async def track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} requested track")
    if update.callback_query:
        message_obj = update.callback_query.message
    else:
        message_obj = update.message
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Updated DB query with full fields
    cursor.execute("""
     SELECT
     user_name, premium_processing,
     application_date, approval_date,
     card_produced_date, card_shipped_date, card_delivered_date
     FROM applications
     ORDER BY application_date
     """)
    applications = cursor.fetchall()
    
    delivered_cards = []
    pending_apps = []
    
    for app in applications:
        (
            user_name, premium,
            app_date, appr_date,
            produced_date, shipped_date, delivered_date
        ) = app
        
        data = {
            "user_name": user_name,
            "premium_processing": premium,
            "application_date": app_date,
            "approved_date": appr_date,
            "card_produced": produced_date,
            "card_shipped": shipped_date,
            "card_delivered": delivered_date
        }
        
        if delivered_date:
            delivered_cards.append(data)
        else:
            pending_apps.append(data)
    
    # Define maximum number of applications per message
    MAX_APPS_PER_MESSAGE = 20
    TELEGRAM_MAX_LENGTH = 4000  # Setting slightly below the 4096 limit to be safe
    
    # Function to format a single application
    def format_application(app, index, is_delivered=False):
        formatted_text = f"🔷 *Application #{index} – {app['user_name']}*\n"
        formatted_text += f"1. Premium Processing: {app['premium_processing']}\n"
        formatted_text += f"2. Receipt Date: {app['application_date']}\n"
        
        if is_delivered:
            formatted_text += f"3. Approved Date: {app['approved_date']}\n"
            formatted_text += f"4. Card Produced: {app['card_produced'] if app['card_produced'] else 'Pending'}\n"
            formatted_text += f"5. Card Shipped: {app['card_shipped'] if app['card_shipped'] else 'Pending'}\n"
            formatted_text += f"6. Card Delivered: {app['card_delivered']}\n\n"
        else:
            if app['approved_date']:
                formatted_text += f"3. Approved Date: {app['approved_date']}\n"
                formatted_text += f"4. Card Produced: {app['card_produced'] if app['card_produced'] else 'Pending'}\n"
                formatted_text += f"5. Card Shipped: {app['card_shipped'] if app['card_shipped'] else 'Pending'}\n"
                formatted_text += f"6. Status: Waiting for card\n\n"
            else:
                formatted_text += f"3. Status: Pending approval\n\n"
                
        return formatted_text
    
    # Send messages in chunks
    async def send_message_chunks(category_title, app_list, is_delivered=False):
        if not app_list:
            return
            
        # Initialize the first message with the category title
        current_message = f"{category_title}\n\n"
        current_count = 0
        
        for i, app in enumerate(app_list, 1):
            app_text = format_application(app, i, is_delivered)
            
            # Check if adding this application would exceed either the max count or max length
            if current_count >= MAX_APPS_PER_MESSAGE or len(current_message + app_text) > TELEGRAM_MAX_LENGTH:
                # Send the current message and start a new one
                await message_obj.reply_text(current_message, parse_mode="Markdown")
                current_message = app_text
                current_count = 1
            else:
                current_message += app_text
                current_count += 1
        
        # Send any remaining message
        if current_message:
            await message_obj.reply_text(current_message, parse_mode="Markdown")
    
    # Handle the case where there are no applications
    if not delivered_cards and not pending_apps:
        await message_obj.reply_text("No applications tracked yet. Use /add to begin tracking your application.")
    else:
        # Send delivered applications
        await send_message_chunks("📬 *DELIVERED EAD CARDS* 📬", delivered_cards, True)
        
        # Send pending applications
        await send_message_chunks("🕒 *PROCESSING APPLICATIONS* 🕒", pending_apps, False)
    
    conn.close()