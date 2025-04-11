from telegram.ext import CommandHandler 

from handlers.start import start_handler
from handlers.help import help_handler
from handlers.track import track_handler
from handlers.clear import clear_handler


command_handlers = [
    CommandHandler("start", start_handler),
    CommandHandler("help", help_handler),
    CommandHandler("track", track_handler),
    CommandHandler("clear", clear_handler),
]