from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, ConversationHandler, filters, ContextTypes
from database import get_connection
from datetime import datetime

# Define conversation states
NAME, APPLICATION_DATE, APPROVAL_DATE, CARD_RECEIVED_DATE = range(4)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Please tell me your name to start tracking your application."
    )
    return NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Enter your OPT application date (YYYY-MM-DD):")
    return APPLICATION_DATE

async def receive_application_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_text = update.message.text
    try:
        application_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        context.user_data['application_date'] = application_date
        await update.message.reply_text("Enter the approval date (YYYY-MM-DD) or type 'pending':")
        return APPROVAL_DATE
    except ValueError:
        await update.message.reply_text("Invalid format. Use YYYY-MM-DD.")
        return APPLICATION_DATE

async def receive_approval_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    approval_text = update.message.text
    if approval_text.lower() == 'pending':
        context.user_data['approval_date'] = None
        context.user_data['card_received_date'] = None
        await save_application(update, context)
        return ConversationHandler.END
    else:
        try:
            approval_date = datetime.strptime(approval_text, "%Y-%m-%d").date()
            context.user_data['approval_date'] = approval_date
            await update.message.reply_text("When did you receive your EAD card? Enter the date (YYYY-MM-DD) or type 'pending':")
            return CARD_RECEIVED_DATE
        except ValueError:
            await update.message.reply_text("Invalid format. Use YYYY-MM-DD.")
            return APPROVAL_DATE

async def receive_card_received_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    card_text = update.message.text
    context.user_data['card_received_date'] = None if card_text.lower() == 'pending' else datetime.strptime(card_text, "%Y-%m-%d").date()
    await save_application(update, context)
    return ConversationHandler.END

async def save_application(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO applications (user_id, name, application_date, approval_date, card_received_date) VALUES (%s, %s, %s, %s, %s)",
        (update.effective_user.id, context.user_data['name'], context.user_data['application_date'], context.user_data['approval_date'], context.user_data['card_received_date'])
    )
    conn.commit()
    conn.close()
    await update.message.reply_text("Your application data has been saved. Use /track to view all applications!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled. Use /add to begin tracking your application.")
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add", add)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        APPLICATION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_application_date)],
        APPROVAL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_approval_date)],
        CARD_RECEIVED_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_card_received_date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
