from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, ConversationHandler, filters, ContextTypes
from database import get_connection
from datetime import datetime
from database import get_or_create_user

# Define conversation states
NAME, APPLICATION_DATE, APPROVAL_DATE, CARD_RECEIVED_DATE = range(4)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    # Check if user already exists
    user_name = get_or_create_user(user_id)
    
    # Determine the message object based on whether this is a callback query or direct command
    if update.callback_query:
        message_obj = update.callback_query.message
    else:
        message_obj = update.message
    
    context.user_data['application_date'] = None
    context.user_data['approval_date'] = None
    context.user_data['card_produced_date'] = None
    context.user_data['card_shipped_date'] = None
    context.user_data['card_delivered_date'] = None

    if user_name:
        # User exists, use their name
        context.user_data['user_name'] = user_name
        await message_obj.reply_text(
            f"Hey {user_name}! Let's track your OPT application.\n"
            f"Enter your OPT application date (YYYY-MM-DD) or type 'pending':"
        )
        return APPLICATION_DATE
    else:
        # New user, ask for their name
        await message_obj.reply_text(
            "Please tell me your name to start tracking your application."
        )
        return NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    name = update.message.text
    
    # Save the user to the database
    get_or_create_user(user_id, name)
    
    context.user_data['user_name'] = name
    await update.message.reply_text("Enter your OPT application date (YYYY-MM-DD) or type 'pending':")
    return APPLICATION_DATE

async def receive_application_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_text = update.message.text
    if date_text.lower() == "pending":
        await save_application(update, context)
        return ConversationHandler.END
    try:
        application_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        context.user_data['application_date'] = application_date
        await update.message.reply_text("Enter the approval date (YYYY-MM-DD) or type 'pending':")
        return APPROVAL_DATE
    except ValueError:
        await update.message.reply_text("Invalid format. Use YYYY-MM-DD or type 'pending'.")
        return APPLICATION_DATE

async def receive_approval_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    approval_text = update.message.text
    
    if approval_text.lower() == "pending":
        context.user_data['card_produced_date'] = None
        context.user_data['card_shipped_date'] = None
        context.user_data['card_delivered_date'] = None
        await save_application(update, context)
        return ConversationHandler.END
    
    try:
        approval_date = datetime.strptime(approval_text, "%Y-%m-%d").date()
        context.user_data['approval_date'] = approval_date
        await update.message.reply_text("When did you receive your EAD card? Enter the date (YYYY-MM-DD) or type 'pending':")
        return CARD_RECEIVED_DATE
    except ValueError:
        await update.message.reply_text("Invalid format. Use YYYY-MM-DD or type 'pending'.")
        return APPROVAL_DATE

async def receive_card_received_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    card_text = update.message.text
    
    if card_text.lower() == "pending":
        context.user_data['card_produced_date'] = None
        context.user_data['card_shipped_date'] = None
        context.user_data['card_delivered_date'] = None
    else:
        try:
            context.user_data['card_produced_date'] = datetime.strptime(card_text, "%Y-%m-%d").date()
        except ValueError:
            await update.message.reply_text("Invalid format. Use YYYY-MM-DD or type 'pending'.")
            return CARD_RECEIVED_DATE
    
    await save_application(update, context)
    return ConversationHandler.END

async def save_application(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE applications SET application_date = %s, approval_date = %s, card_produced_date = %s WHERE user_id = %s",
        (context.user_data['application_date'], context.user_data['approval_date'], context.user_data['card_produced_date'], update.effective_user.id)
    )
    print(context.user_data['application_date'], context.user_data['approval_date'], context.user_data['card_produced_date'])
    conn.commit()
    conn.close()
    await update.message.reply_text("Your application data has been saved. Use /track to view all applications!")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled. Use /add to begin tracking your application.")
    return ConversationHandler.END

add_new_opt = ConversationHandler(
    entry_points=[CommandHandler("add", add)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        APPLICATION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_application_date)],
        APPROVAL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_approval_date)],
        CARD_RECEIVED_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_card_received_date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)