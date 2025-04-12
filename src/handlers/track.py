# In src/handlers/track.py
from telegram import Update
from telegram.ext import ContextTypes
import logging 
from database import get_connection

logger = logging.getLogger(__name__)


async def track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} requested track")
    
    # Get the message object based on whether this is from a callback or direct command
    if update.callback_query:
        message_obj = update.callback_query.message
    else:
        message_obj = update.message
    
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all applications
    cursor.execute("SELECT name, application_date, approval_date, card_received_date FROM applications ORDER BY application_date")
    applications = cursor.fetchall()

    # Separate into categories: delivered cards, approved but waiting for card, and pending
    delivered_cards = []
    approved_waiting = []
    pending_apps = []

    for name, app_date, appr_date, card_date in applications:
        if card_date:  # Card delivered
            delivered_cards.append((name, app_date, appr_date, card_date))
        elif appr_date:  # Approved but waiting for card
            approved_waiting.append((name, app_date, appr_date))
        else:  # Pending approval
            pending_apps.append((name, app_date))

    # Start building the message
    message = ""
    
    # Format delivered cards section
    if delivered_cards:
        message += "📬 DELIVERED EAD CARDS 📬\n\n"
        for i, (name, app_date, appr_date, card_date) in enumerate(delivered_cards, 1):
            message += f"🔹 Application #{i} - {name}\n"
            message += f"1. Receipt date: {app_date.strftime('%m/%d/%Y')}\n"
            message += f"2. Approved date: {appr_date.strftime('%m/%d/%Y')}\n"
            message += f"3. Card delivered: {card_date.strftime('%m/%d/%Y')}\n\n"
    
    # Format approved but waiting section
    if approved_waiting:
        message += "⏳ APPROVED APPLICATIONS (CARD PENDING) ⏳\n\n"
        for i, (name, app_date, appr_date) in enumerate(approved_waiting, 1):
            message += f"🔹 Application #{i} - {name}\n"
            message += f"1. Receipt date: {app_date.strftime('%m/%d/%Y')}\n"
            message += f"2. Approved date: {appr_date.strftime('%m/%d/%Y')}\n"
            message += f"3. Card status: Waiting for delivery\n\n"
    
    # Format pending applications section
    if pending_apps:
        message += "🕒 PENDING APPLICATIONS 🕒\n\n"
        for i, (name, app_date) in enumerate(pending_apps, 1):
            message += f"🔹 Application #{i} - {name}\n"
            message += f"1. Receipt date: {app_date.strftime('%m/%d/%Y')}\n"
            message += f"2. Status: Pending approval\n\n"
    
    # If there are no applications, let the user know
    if not delivered_cards and not approved_waiting and not pending_apps:
        message = "No applications tracked yet. Use /add to begin tracking your application."
    
    conn.close()
    
    # Send the formatted message
    await message_obj.reply_text(message)