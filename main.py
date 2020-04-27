import config

from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = config.BOT_TOEKN
ADMIN_USERNAMES = config.ADMIN_USERNAMES

#TODO: Enum menu
USER_MAIN_MANU = 0
ADMIN_MAIN_MANU = 100
ADD_CASE = 101
DEL_CASE = 102
UPDATE_CASE = 103
GET_CASE_ID = 104
ALL_CASE_INFO = 105
GET_VISITED_DATE = 106
ADMIN_TIMER = 107
SET_PET_NAME = 108

#TODO: Redis server
patients = {}

#TODO Better keyboard -> conversation Handler
reply_keyboard = [['new case', 'update case'],
                  ['del case', 'all case info'],
                  ['broadcast', 'narrowcast']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

def admin_start(update, context):
    usr = update.effective_user
    username = usr['username']
    if is_admin(username):
        update.message.reply_text(f'Welcome Back {username}')
        logger.info('%s logged in as the admin user', username)
        admin_main_menu(update)
        return ADMIN_MAIN_MANU
    else:
        update.message.reply_text('Hmmm... How did you find about this command? ADMINS ONLY')
        logger.warning('%s tried to login in as administrator')

def admin_main_menu(update):
    update.message.reply_text(f'What do you want to do?', reply_markup=markup)

def admin_add_case(update, context):
    update.message.reply_text("Please Enter the case ID")
    return GET_CASE_ID 

def admin_del_case(update, context):
    return

def admin_update_case(update, context):
    return UPDATE_CASE

def admin_all_case_info(update, context):
    print(patients)
    admin_main_menu(update)
    return ADMIN_MAIN_MANU

def is_admin(user):
    return user in ADMIN_USERNAMES

def get_case_id(update, context):
    case_id = update.message.text

    if case_exsits(case_id):
        update.message.reply_text(f'a case with this id: {case_id} already exsists!')
        update.message.reply_text(f'do you want to submit a new visit?')
        return UPDATE_CASE
    else:
        update.message.reply_text(f'a new case with id #{case_id} has been created')
        context.user_data['case_id'] = case_id
        update.message.reply_text('enter the Pet name')
        return SET_PET_NAME

def set_pet_name(update, context):
    pet_name = update.message.text
    context.user_data['pet_name'] = pet_name
    update.message.reply_text(f'Nice Name, I\'ll remember that, enter {pet_name}\'s visit')
    return GET_VISITED_DATE
 
def case_exsits(case_id):
    return case_id in patients

def unknown_command(update, context):
    update.message.reply_text('command not found! Please try agian.')
    return USER_MAIN_MANU

def update_case_date(update, context):
    visit_date = update.message.text
    context.user_data['date'] = visit_date
    update.message.reply_text('New Case had been created! Set Timer')
    return ADMIN_TIMER

def set_reminder_timer(update, context):
    next_alarm = update.message.text
    pet_name = context.user_data['pet_name']
    case_id = context.user_data['case_id']
    latest_visit = context.user_data['date']
    patients[case_id] = {}
    patients[case_id] = {'id': None,
                                    'first_name': None,
                                    'is_bot': False,
                                    'last_name': None,
                                    'username': None, 
                                    'language_code': None,
                                    'next_alarm': next_alarm,
                                    'latest_visit': latest_visit,
                                    'visit_history': [latest_visit],
                                    'pet_name': pet_name}
    
    del context.user_data['case_id']
    
    update.message.reply_text(f'I created a profile for {pet_name}, here is the details {patients[case_id]}')

    admin_main_menu(update)
    return ADMIN_MAIN_MANU

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    #admin_handler = CommandHandler('admin_start', admin_start)
    
    admin_handler = ConversationHandler(
        entry_points = [CommandHandler('admin_start', admin_start)],

        states= {
            ADMIN_MAIN_MANU:[MessageHandler(Filters.regex('^new case$'),
                            admin_add_case), 
                            MessageHandler(Filters.regex('^update case$'),
                            admin_update_case),
                            MessageHandler(Filters.regex('^del case$'),
                            admin_del_case), 
                            MessageHandler(Filters.regex('^all case info$'),
                            admin_all_case_info)
            ],
            GET_CASE_ID:[MessageHandler(Filters.text,
                                         get_case_id)
            ],
            SET_PET_NAME:[MessageHandler(Filters.text,
                                                set_pet_name)
            ],
            GET_VISITED_DATE:[MessageHandler(Filters.text,
                                                update_case_date)
            ],
            ADMIN_TIMER:[MessageHandler(Filters.text,
                                         set_reminder_timer)
            ]
        },

        fallbacks=[MessageHandler(Filters.regex('^done$'), unknown_command)]
    )

    dp.add_handler(admin_handler)
    updater.start_polling()

    updater.idle()

    dp.add_handler(admin_handler)
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()