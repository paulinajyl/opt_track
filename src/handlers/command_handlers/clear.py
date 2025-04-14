from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import get_connection
import logging 

logger = logging.getLogger(__name__)

async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} cleared entries")
    user_id = update.effective_user.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("Your application data has been cleared.")
