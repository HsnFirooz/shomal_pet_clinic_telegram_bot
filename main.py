import config

from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = config.TOEKN
ADMIN_USERNAME = config.admin_username

admin_keyboard = [['add new case', 'case history']]

ADMIN_MAIN_MENU, ADD_CASE_ID, CASE_HISTORY = range(3)

def admin_start(update, context):
    usr = update.effective_user
    username = usr['username']
    if is_admin(username):
        update.message.reply_text(f'Welcome Back {username}')
        logger.info('%s logged in as the admin user', username)
    else:
        update.message.reply_text('Hmmm... How did you find about this command? ADMINS ONLY')
        logger.info('%s tried to login in as administrator')
    pass

def is_admin(user):
    return user in ADMIN_USERNAME

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    admin_handler = CommandHandler('admin_start', admin_start)
    
    dp.add_handler(admin_handler)
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()