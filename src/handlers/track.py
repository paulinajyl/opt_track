from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import logging 
from database import get_connection

logger = logging.getLogger(__name__)



async def track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} requested track")
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all applications
    cursor.execute("SELECT name, application_date, approval_date, card_received_date FROM applications ORDER BY application_date")
    applications = cursor.fetchall()

    # Separate approved and pending applications
    approved_apps = []
    pending_apps = []

    for name, app_date, appr_date, card_date in applications:
        if appr_date:  # If the application is approved
            approved_apps.append((name, app_date, appr_date, card_date))
        else:  # If the application is pending approval
            pending_apps.append((name, app_date))

    # Start building the message
    message = "------Approved Applications------\n"

    # Format approved applications
    for name, app_date, appr_date, card_date in approved_apps:
        message += f"{name} applied on {app_date.strftime('%B %d')}, got approved on {appr_date.strftime('%B %d')}, "
        if card_date:
            message += f"card received on {card_date.strftime('%B %d')}\n"
        else:
            message += "waiting for card\n"

    # Add a separator if there are any pending applications
    if pending_apps:
        message += "\n------Pending Applications------\n"

        # Format pending applications
        for name, app_date in pending_apps:
            message += f"{name} applied on {app_date.strftime('%B %d')}\n"

    # If there are no applications, let the user know
    if not approved_apps and not pending_apps:
        message = "No applications tracked yet.\n"

    conn.close()

    # Send the formatted message to the user
    await update.message.reply_text(message)
