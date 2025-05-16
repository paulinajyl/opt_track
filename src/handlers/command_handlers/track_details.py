from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from database import get_connection
from datetime import datetime

logger = logging.getLogger(__name__)

# Constants
TELEGRAM_MAX_LENGTH = 4000  # Setting slightly below the 4096 limit to be safe
MAX_APPS_PER_MESSAGE = 20
PAGE_SIZE = 30  # Number of applications to show per page

# Main handler that will handle button selection
async def track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} requested track")
    
    # Determine if this is from a callback or direct command
    callback_data = None
    if update.callback_query:
        message_obj = update.callback_query.message
        callback_data = update.callback_query.data
        # Answer callback query to stop the loading indicator
        await update.callback_query.answer()
    else:
        message_obj = update.message
    
    # If no specific callback, show the main menu
    if not callback_data or callback_data == "track_main":
        await show_tracking_menu(message_obj)
        return
    
    # Parse callback data to determine which view to show
    parts = callback_data.split('_')
    if len(parts) < 2:
        await show_tracking_menu(message_obj)
        return
    
    # Load applications from database only once
    applications = load_applications_from_db()
    
    # Process paging if present in callback
    page = 1
    if len(parts) >= 3 and parts[-2] == "page":
        try:
            page = int(parts[-1])
            callback_data = '_'.join(parts[:-2])  # Remove page info from callback
        except ValueError:
            page = 1
    
    # Handle different view types
    if callback_data == "track_delivered":
        await show_delivered_cards(message_obj, applications, page)
    elif callback_data == "track_waiting":
        await show_waiting_cards(message_obj, applications, page)
    elif callback_data == "track_pending":
        await show_pending_approval(message_obj, applications, page)
    elif callback_data == "track_all":
        await show_all_applications(message_obj, applications, page)
    else:
        await show_tracking_menu(message_obj)

# Show the main tracking menu with buttons
async def show_tracking_menu(message_obj):
    keyboard = [
        [
            InlineKeyboardButton("📬 Delivered Cards", callback_data="track_delivered"),
            InlineKeyboardButton("⏳ Waiting for Card", callback_data="track_waiting")
        ],
        [
            InlineKeyboardButton("🗿 Pending Approval", callback_data="track_pending"),
            InlineKeyboardButton("📋 All Applications", callback_data="track_all")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_obj.reply_text("Choose a category to view:", reply_markup=reply_markup)

# Load all applications from the database
def load_applications_from_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
     SELECT
     user_name, premium_processing,
     application_date, approval_date,
     card_produced_date, card_shipped_date, card_delivered_date
     FROM applications
     ORDER BY application_date
     """)
    
    applications = []
    for app in cursor.fetchall():
        (
            user_name, premium,
            app_date, appr_date,
            produced_date, shipped_date, delivered_date
        ) = app
        
        applications.append({
            "user_name": user_name,
            "premium_processing": "Yes" if premium else "No",
            "application_date": app_date,
            "approved_date": appr_date,
            "card_produced": produced_date,
            "card_shipped": shipped_date,
            "card_delivered": delivered_date
        })
    
    conn.close()
    return applications

# Calculate total processing time
def calculate_total_time(start_date, end_date):
    if not start_date or not end_date:
        return "N/A"
    
    try:
        # Convert string dates to datetime objects if they are strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            
        delta = end_date - start_date
        return f"{delta.days} days"
    except Exception as e:
        logger.error(f"Error calculating total time: {e}")
        return "Error"

# Format applications with pagination
def get_pagination_keyboard(callback_prefix, current_page, total_pages):
    keyboard = []
    nav_buttons = []
    
    # Add navigation buttons (Previous/Next)
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"{callback_prefix}_page_{current_page-1}"))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"{callback_prefix}_page_{current_page+1}"))
    
    # Add nav buttons to keyboard if there are any
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Always add back button in its own row
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="track_main")])
    
    return InlineKeyboardMarkup(keyboard)

# Show delivered cards
async def show_delivered_cards(message_obj, applications, page=1):
    delivered = [app for app in applications if app["card_delivered"]]
    
    if not delivered:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="track_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message_obj.reply_text("No delivered cards found.", reply_markup=reply_markup)
        return
    
    # Sort by delivery date, newest first
    delivered.sort(key=lambda x: x["card_delivered"] if x["card_delivered"] else "", reverse=True)
    
    # Calculate total pages and slice for current page
    total_pages = max(1, (len(delivered) + PAGE_SIZE - 1) // PAGE_SIZE)
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(delivered))
    current_page_apps = delivered[start_idx:end_idx]
    
    # Format message
    message = f"📬 DELIVERED EAD CARDS ({len(delivered)}) 📬 - Page {page}/{total_pages}\n\n"
    
    for app in current_page_apps:
        total_time = calculate_total_time(app["application_date"], app["card_delivered"])
        message += f"🔷 {app['user_name']}\n"
        message += f"Receipt: {app['application_date']}\n"
        message += f"Premium: {app['premium_processing']}\n"
        message += f"Approved: {app['approved_date'] or 'N/A'}\n"
        message += f"Card Produced: {app['card_produced'] or 'N/A'}\n"
        message += f"Card Shipped: {app['card_shipped'] or 'N/A'}\n"
        message += f"Card Delivered: {app['card_delivered']}\n"
        message += f"Total Time: {total_time}\n\n"
    
    # Add pagination
    reply_markup = get_pagination_keyboard("track_delivered", page, total_pages)
    
    await message_obj.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

# Show applications waiting for card (approved but not delivered)
async def show_waiting_cards(message_obj, applications, page=1):
    waiting = [
        app for app in applications 
        if app["approved_date"] and not app["card_delivered"]
    ]
    
    if not waiting:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="track_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message_obj.reply_text("No applications waiting for card.", reply_markup=reply_markup)
        return
    
    # Sort by approval date, newest first
    waiting.sort(key=lambda x: x["approved_date"] if x["approved_date"] else "", reverse=True)
    
    # Categorize waiting applications
    waiting_delivery = []
    waiting_shipment = []
    waiting_production = []
    
    for app in waiting:
        if app["card_shipped"]:
            waiting_delivery.append(app)
        elif app["card_produced"]:
            waiting_shipment.append(app)
        else:
            waiting_production.append(app)
    
    # Combine all categories in order
    all_waiting = waiting_delivery + waiting_shipment + waiting_production
    
    # Calculate total pages and slice for current page
    total_pages = max(1, (len(all_waiting) + PAGE_SIZE - 1) // PAGE_SIZE)
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(all_waiting))
    current_page_apps = all_waiting[start_idx:end_idx]
    
    # Format message
    message = f"⏳ WAITING FOR CARD ({len(all_waiting)}) ⏳ - Page {page}/{total_pages}\n\n"
    
    for app in current_page_apps:
        if app["card_shipped"]:
            status = "Waiting for delivery"
        elif app["card_produced"]:
            status = "Waiting for shipment"
        else:
            status = "Waiting for production"
            
        message += f"🔷 {app['user_name']} - {status}\n"
        message += f"Receipt: {app['application_date']}\n"
        message += f"Premium: {app['premium_processing']}\n"
        message += f"Approved: {app['approved_date'] or 'N/A'}\n"
        message += f"Card Produced: {app['card_produced'] or 'N/A'}\n"
        
        if app["card_produced"]:
            message += f"Shipped: {app['card_shipped'] or 'N/A'}\n\n"
        else:
            message += "\n"
    
    # Add pagination
    reply_markup = get_pagination_keyboard("track_waiting", page, total_pages)
    
    await message_obj.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

# Show applications pending approval
async def show_pending_approval(message_obj, applications, page=1):
    pending = [app for app in applications if not app["approved_date"]]
    
    if not pending:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="track_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message_obj.reply_text("No applications pending approval.", reply_markup=reply_markup)
        return
    
    # Sort by application date, newest first
    pending.sort(key=lambda x: x["application_date"] if x["application_date"] else "", reverse=True)
    
    # Calculate total pages and slice for current page
    total_pages = max(1, (len(pending) + PAGE_SIZE - 1) // PAGE_SIZE)
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(pending))
    current_page_apps = pending[start_idx:end_idx]
    
    # Format message
    message = f"🗿 PENDING APPROVAL ({len(pending)}) 🗿 - Page {page}/{total_pages}\n\n"
    
    for app in current_page_apps:
        message += f"🔷 {app['user_name']}\n"
        message += f"Receipt: {app['application_date']}\n"
        message += f"Premium: {app['premium_processing']}\n"

    # Add pagination
    reply_markup = get_pagination_keyboard("track_pending", page, total_pages)
    
    await message_obj.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

# Show all applications
async def show_all_applications(message_obj, applications, page=1):
    if not applications:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="track_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message_obj.reply_text("No applications found.", reply_markup=reply_markup)
        return
    
    # Sort by application date, newest first
    applications.sort(key=lambda x: x["application_date"] if x["application_date"] else "", reverse=True)
    
    # Calculate total pages and slice for current page
    total_pages = max(1, (len(applications) + PAGE_SIZE - 1) // PAGE_SIZE)
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(applications))
    current_page_apps = applications[start_idx:end_idx]
    
    # Format message
    message = f"📋 ALL APPLICATIONS ({len(applications)}) 📋 - Page {page}/{total_pages}\n\n"
    
    for app in current_page_apps:
        status = "Delivered" if app["card_delivered"] else (
            "Waiting for delivery" if app["card_shipped"] else (
            "Waiting for shipment" if app["card_produced"] else (
            "Waiting for production" if app["approved_date"] else "Pending approval")))
        
        message += f"🔷 {app['user_name']} - {status}\n"
        message += f"Receipt: {app['application_date']}\n"
        message += f"Premium: {app['premium_processing']}\n"
        
        if app["approved_date"]:
            message += f"Approved: {app['approved_date']}\n"
            
            if app["card_produced"]:
                message += f"Produced: {app['card_produced']}\n"
                
                if app["card_shipped"]:
                    message += f"Shipped: {app['card_shipped']}\n"
                    
                    if app["card_delivered"]:
                        message += f"Delivered: {app['card_delivered']}\n"
                        message += f"Total Time: {calculate_total_time(app['application_date'], app['card_delivered'])}\n"
        
        message += "\n"
    
    # Add pagination
    reply_markup = get_pagination_keyboard("track_all", page, total_pages)
    
    await message_obj.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")