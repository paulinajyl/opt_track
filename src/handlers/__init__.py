# In src/handlers/__init__.py
from telegram.ext import CommandHandler, CallbackQueryHandler

from handlers.command_handlers.start import start_handler
from handlers.command_handlers.help import help_handler
from handlers.command_handlers.track import track_handler
from handlers.command_handlers.clear import clear_handler

from handlers.conversation_handlers.add_new_opt_app_flow import add_new_opt

from handlers.callbacks import button_callback_handler

command_handlers = [
    CommandHandler("start", start_handler),
    CommandHandler("help", help_handler),
    CommandHandler("track", track_handler),
    CommandHandler("clear", clear_handler),
    CallbackQueryHandler(button_callback_handler),  
]

conversation_handlers = [
    add_new_opt,
]