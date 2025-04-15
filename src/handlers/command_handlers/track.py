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
            
    # Start building the message
    message = ""
    
    # Format delivered section
    if delivered_cards:
        message += "📬 *DELIVERED EAD CARDS* 📬\n\n"
        for i, app in enumerate(delivered_cards, 1):
            message += (
                f"🔷 *Application #{i} – {app['user_name']}*\n"
                f"1. Premium Processing: {app['premium_processing']}\n"
                f"2. Receipt Date: {app['application_date']}\n"
                f"3. Approved Date: {app['approved_date']}\n"
                f"4. Card Produced: {app['card_produced'] if app['card_produced'] else 'Pending'}\n"
                f"5. Card Shipped: {app['card_shipped'] if app['card_shipped'] else 'Pending'}\n"
                f"6. Card Delivered: {app['card_delivered']}\n\n"
            )
            
    # Format combined in-progress applications section
    if pending_apps:
        message += "🕒 *PROCESSING APPLICATIONS* 🕒\n\n"
        for i, app in enumerate(pending_apps, 1):
            status = "Waiting for card" if app['approved_date'] else "Pending approval"
                
            message += (
                f"🔷 *Application #{i} – {app['user_name']}*\n"
                f"1. Premium Processing: {app['premium_processing']}\n"
                f"2. Receipt Date: {app['application_date']}\n"
            )
            
            if app['approved_date']:
                message += f"3. Approved Date: {app['approved_date']}\n"
            
            if app['approved_date']:
                message += f"4. Produced Date: {app['card_produced']}\n"
            
            if app['approved_date']:
                message += f"5. Shipped Date: {app['card_shipped']}\n"
                
            message += f"{3 if not app['approved_date'] else 4}. Status: {status}\n\n"
            
    if not delivered_cards and not pending_apps:
        message = "No applications tracked yet. Use /add to begin tracking your application."
        
    conn.close()
    await message_obj.reply_text(message, parse_mode="Markdown")