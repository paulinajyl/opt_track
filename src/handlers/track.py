from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import logging 
from database import get_connection

logger = logging.getLogger(__name__)

async def track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} requested track")
    user_id = update.effective_user.id
    conn = get_connection()
    cursor = conn.cursor()
    
    # First, get the user's name
    cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        await update.message.reply_text("You haven't added any applications yet. Use /add to start tracking your application.")
        conn.close()
        return
    
    # Now get all applications
    cursor.execute("""
        SELECT application_date, approval_date, card_received_date 
        FROM applications 
        WHERE user_id = %s
        ORDER BY application_date
    """, (user_id,))
    
    applications = cursor.fetchall()
    
    if not applications:
        await update.message.reply_text("You haven't added any applications yet. Use /add to start tracking your application.")
        conn.close()
        return
    
    # Separate approved and pending applications
    approved_apps = []
    pending_apps = []
    user_name = user[0]  # Get the user's name from the users table

    for app_date, appr_date, card_date in applications:
        if appr_date:  # If the application is approved
            approved_apps.append((app_date, appr_date, card_date))
        else:  # If the application is pending approval
            pending_apps.append((app_date))

    # Start building the message
    message = "------Approved Applications------\n"

    # Format approved applications
    for app_date, appr_date, card_date in approved_apps:
        # Handle application_date when it's "pending"
        app_date_str = app_date if isinstance(app_date, str) else app_date.strftime('%B %d')
        
        message += f"{user_name} applied on {app_date_str}, got approved on {appr_date.strftime('%B %d')}, "
        if card_date:
            message += f"card received on {card_date.strftime('%B %d')}\n"
        else:
            message += "waiting for card\n"

    # Add a separator if there are any pending applications
    if pending_apps:
        message += "\n------Pending Applications------\n"

        # Format pending applications
        for app_date in pending_apps:
            # Handle application_date when it's "pending"
            app_date_str = app_date if isinstance(app_date, str) else app_date.strftime('%B %d')
            message += f"{user_name} applied on {app_date_str}\n"

    # If there are no applications, let the user know
    if not approved_apps and not pending_apps:
        message = "No applications tracked yet.\n"

    conn.close()

    # Send the formatted message to the user
    await update.message.reply_text(message)