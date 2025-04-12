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
            name, application_type, premium_processing, 
            application_date, approval_date, 
            card_produced_date, card_shipped_date, card_delivered_date 
        FROM applications
        ORDER BY application_date
    """)
    applications = cursor.fetchall()

    delivered_cards = []
    approved_waiting = []
    pending_apps = []

    for app in applications:
        (
            name, app_type, premium, 
            app_date, appr_date, 
            produced_date, shipped_date, delivered_date
        ) = app

        data = {
            "name": name,
            "application_type": app_type,
            "premium_processing": premium,
            "receipt_date": app_date,
            "approved_date": appr_date,
            "card_produced": produced_date,
            "card_shipped": shipped_date,
            "card_delivered": delivered_date
        }

        if delivered_date:
            delivered_cards.append(data)
        elif appr_date:
            approved_waiting.append(data)
        else:
            pending_apps.append(data)

    # Start building the message
    message = ""

    # Format delivered section
    if delivered_cards:
        message += "📬 *DELIVERED EAD CARDS* 📬\n\n"
        for i, app in enumerate(delivered_cards, 1):
            message += (
                f"🔷 *Application #{i} – {app['name']}*\n"
                f"1. Application Type: {app['application_type']}\n"
                f"2. Premium Processing: {app['premium_processing']}\n"
                f"3. Receipt Date: {app['receipt_date'].strftime('%m/%d/%Y')}\n"
                f"4. Approved Date: {app['approved_date'].strftime('%m/%d/%Y')}\n"
                f"5. Card Produced: {app['card_produced'].strftime('%m/%d/%Y') if app['card_produced'] else 'Pending'}\n"
                f"6. Card Shipped: {app['card_shipped'].strftime('%m/%d/%Y') if app['card_shipped'] else 'Pending'}\n"
                f"7. Card Delivered: {app['card_delivered'].strftime('%m/%d/%Y')}\n\n"
            )

    # Format approved waiting
    if approved_waiting:
        message += "⏳ *APPROVED APPLICATIONS (CARD PENDING)* ⏳\n\n"
        for i, app in enumerate(approved_waiting, 1):
            message += (
                f"🔷 *Application #{i} – {app['name']}*\n"
                f"1. Application Type: {app['application_type']}\n"
                f"2. Premium Processing: {app['premium_processing']}\n"
                f"3. Receipt Date: {app['receipt_date'].strftime('%m/%d/%Y')}\n"
                f"4. Approved Date: {app['approved_date'].strftime('%m/%d/%Y')}\n"
                f"5. Card Produced: {app['card_produced'].strftime('%m/%d/%Y') if app['card_produced'] else 'Pending'}\n"
                f"6. Card Shipped: {app['card_shipped'].strftime('%m/%d/%Y') if app['card_shipped'] else 'Pending'}\n"
                f"7. Card Delivered: Pending\n\n"
            )

    # Format pending applications
    if pending_apps:
        message += "🕒 *PENDING APPLICATIONS* 🕒\n\n"
        for i, app in enumerate(pending_apps, 1):
            message += (
                f"🔷 *Application #{i} – {app['name']}*\n"
                f"1. Application Type: {app['application_type']}\n"
                f"2. Premium Processing: {app['premium_processing']}\n"
                f"3. Receipt Date: {app['receipt_date'].strftime('%m/%d/%Y')}\n"
                f"4. Status: Pending approval\n\n"
            )

    if not delivered_cards and not approved_waiting and not pending_apps:
        message = "No applications tracked yet. Use /add to begin tracking your application."

    conn.close()

    await message_obj.reply_text(message, parse_mode="Markdown")
