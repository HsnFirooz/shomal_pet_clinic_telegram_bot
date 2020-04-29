import config

import redis
import time
import json
import datetime

from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler, CallbackContext)

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
SET_CASE_ID = 104
ALL_CASE_INFO = 105
GET_VISITED_DATE = 106
ADMIN_TIMER = 107
SET_PET_NAME = 108
CASE_MEDICINE = 110
NARROWCAST = 111
NARROWCAST_TEXT = 112
BROADCAST = 113

redis_db = redis.Redis(host='127.0.0.1', port='6379', db=0)

#TODO Better keyboard -> conversation Handler

user_reply_keyboard = [['new case', 'update case'],
                        ['del case', 'all case info'],
                        ['broadcast', 'narrowcast']]
admin_markup = ReplyKeyboardMarkup(user_reply_keyboard, one_time_keyboard=True)

def admin_start(update, context):
    usr = update.effective_user
    username = usr['username']
    if is_admin(username):
        context.bot_data[username] = usr['id']
        update.message.reply_text(f'Welcome Back {username}')
        logger.info('%s logged in as the admin user', username)
        return admin_main_menu(update)
    
    else:
        update.message.reply_text('Hmmm... How did you find about this command? ADMINS ONLY')
        logger.warning('%s tried to login in as administrator', username)

def admin_main_menu(update):
    admin_reply_keyboard = [['new case', 'update case'],
                            ['del case', 'all case info'],
                            ['broadcast', 'narrowcast']]
    admin_markup = ReplyKeyboardMarkup(admin_reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(f'What do you want to do?', reply_markup=admin_markup)
    return ADMIN_MAIN_MANU

def admin_add_case(update, context):
    update.message.reply_text("Please Enter the case ID")
    return SET_CASE_ID 

def admin_del_case(update, context):
    return

def admin_update_case(update, context):
    return UPDATE_CASE

def admin_all_case_info(update, context):
    pass

def is_admin(user):
    return user in ADMIN_USERNAMES

def get_case_id(update, context):
    case_id = update.message.text
    context.user_data['case_id'] = case_id
    if case_exsits(case_id):
        
        update.message.reply_text(f'a case with this id: {case_id} already exsists!')
        update.message.reply_text(f'do you want to submit a new visit?')
        return GET_VISITED_DATE #TODO: Nested Coversation: Yes, No
    else:
        update.message.reply_text(f'a new case with id #{case_id} has been created')
        update.message.reply_text('enter the Pet name')
        return SET_PET_NAME

def set_pet_name(update, context):
    pet_name = update.message.text
    context.user_data['pet_name'] = pet_name
    update.message.reply_text(f'Nice Name, I\'ll remember that, enter {pet_name}\'s visit:',
                                reply_markup=ReplyKeyboardMarkup([['Today']], one_time_keyboard=True))
    return GET_VISITED_DATE
 
def case_exsits(case_id):
    return redis_db.get('case_id')

def unknown_command(update, context):
    update.message.reply_text('command not found! Please try agian.')
    return USER_MAIN_MANU

def update_case_date(update, context): 
    visit_date = update.message.text
    if (visit_date=='Today'): #PICKEL SERIALIZE
        visit_date = time.time()
    else: #Print a nice calander on telegram inline keyboard
        alaki = 2
    context.user_data['date'] = visit_date

    context.user_data['medicine'] = []
    context.user_data['reminder'] = []
    medicine_keyboard = [['A', 'B', 'C'],
                         ['D', 'E', 'F']]
    update.message.reply_text(f'What did you do for her?',
                                reply_markup=ReplyKeyboardMarkup(medicine_keyboard, one_time_keyboard=True))
    return CASE_MEDICINE

def add_case_medicine(update, context):
    medicine = update.message.text
    context.user_data['medicine'].append(medicine)

    update.message.reply_text(f'OK, when she should come back for her {medicine}')

    return ADMIN_TIMER

def create_new_case(update, context):
    pet_name = context.user_data['pet_name']
    case_id = context.user_data['case_id']
    latest_visit = context.user_data['date']
    reminders = context.user_data['reminder']
    medicines = context.user_data['medicine']
    #TODO: append visit and medicins together for better logging
    patient = {
                'guardian': list(),
                'case': {
                    'reminder': reminders,
                    'medicine': medicines,
                    'latest_visit': latest_visit,
                    'visit_history': [latest_visit],
                    'pet_name': pet_name
                }
    }

    context.user_data.clear()
    
    redis_db.set(case_id, json.dumps(patient))
    update.message.reply_text(f'I created a profile for {pet_name}, here is the details {patient}')

    return admin_main_menu(update)

def set_reminder_timer(update, context):
    #TODO: Fix UCT time
    latest_visit = context.user_data['date']
    reminder = update.message.text
    context.user_data['reminder'].append(reminder)
    update.message.reply_text(f'OK, She has to come back in {update.message.text} minutes')

    medicine_keyboard = [['A', 'B', 'C'],
                         ['D', 'E', 'F'],
                         ['/done']]
    update.message.reply_text(f'What did you do for her?',
                                reply_markup=ReplyKeyboardMarkup(medicine_keyboard, one_time_keyboard=True))

    return CASE_MEDICINE

def narrowcast_case_id(update, context):
    update.message.reply_text("Please Enter the case ID")
    return NARROWCAST_TEXT

def broadcast_get_text(update, context):
    update.message.reply_text('What do you want to say to guardians?')
    return BROADCAST

def broadcast_message(update, context):
    for key in redis_db.keys():
        patient = json.loads(redis_db.get(key))
        guardians = patient['guardian']
        if guardians:
            context.user_data['guardians_chat_id'] = []
            for guardian in guardians:
                g_id = guardian['id']
                context.user_data['guardians_chat_id'].append(g_id)
            send_message(update, context)
        else:
            continue

def narrowcast_text(update, context):
    case_id = update.message.text
    patient = redis_db.get(case_id)
    if patient is not None:
        patient = json.loads(patient)
        guardians = patient['guardian']
        if guardians:
            context.user_data['guardians_chat_id'] = []
            for guardian in guardians:
                g_id = guardian['id']
                context.user_data['guardians_chat_id'].append(g_id)
            update.message.reply_text(f'What do you want to say to {case_id} guardians?')
            return NARROWCAST
        else:
            update.message.reply_text(f'There is no registered guardian for {case_id}')
            return admin_main_menu(update)
    else:
        update.message.reply_text('Are you sure about the case id? I didn\'t find anything!')
        return admin_main_menu(update)

def send_message(update, context):
    #TODO: counter
    #TODO: BLOCK exeption
    text = update.message.text
    for chat_id in context.user_data['guardians_chat_id']:
        context.bot.send_message(chat_id=chat_id, text=text)
    update.message.reply_text(f'DONE!')
    context.user_data.clear()
    return admin_main_menu(update)


def user_start(update, context):
    usr = update.effective_user
    name = usr['first_name']
    update.message.reply_text(f'Hello {name}!')
    return user_main_menu(update)

def user_main_menu(update):
    user_keyboard = [['case']]
    update.message.reply_text(f'What do you want to do?',
                                reply_markup=ReplyKeyboardMarkup(user_keyboard, one_time_keyboard=True))
    return USER_MAIN_MANU

def user_add_case(update, context):
    update.message.reply_text("Please Enter the case ID")
    return SET_CASE_ID 

def user_get_case_id(update, context):
    case_id = update.message.text
    patient = redis_db.get(case_id)
    if patient is not None:
        patient = json.loads(patient)
        pet_name = patient['case']['pet_name']
        tg_guardian = update.effective_user
        if tg_guardian not in patient['guardian']:
            patient['guardian'].append(tg_guardian.to_dict())
            redis_db.set(case_id, json.dumps(patient))
            set_user_reminder(update, context,
                              patient['case']['medicine'], 
                              patient['case']['reminder'])
            update.message.reply_text(f'Done! You are now {pet_name} guardian')
            _notify_admins(context, tg_guardian, case_id)
        else:
            update.reply_text('You are already a registered guardian for this {pet_name}')
    else:
        update.message.reply_text('Are you sure about the case id? I didn\'t find anything!')

    return user_main_menu(update)

def send_reminder_message(context: CallbackContext):
    # Remove from medicine and reminder dict
    chat_id = medicine = context.job.context[0]
    medicine = context.job.context[1]
    context.bot.send_message(chat_id=chat_id,
                             text=f'It\'s time for {medicine} for your pet')

def set_user_reminder(update, context, medicine, reminder):
    chat_id = update.message.chat_id
    for m, r in zip(medicine, reminder):
        context.job_queue.run_once(send_reminder_message,
                                    when=int(r), 
                                    context=[chat_id, m])  
        print('setting job')

def _notify_admins(context, guardian, case_id):
    admins = context.bot_data
    for username in admins:
        context.bot.send_message(chat_id = admins[username], text=(f'{guardian} registered! for {case_id} guardian'))

def main():
    #TODO:  
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
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
                            admin_all_case_info),
                            MessageHandler(Filters.regex('^narrowcast$'),
                            narrowcast_case_id),
                            MessageHandler(Filters.regex('^broadcast$'),
                            broadcast_get_text)
            ],
            SET_CASE_ID:[MessageHandler(Filters.text,
                                         get_case_id)
            ],
            SET_PET_NAME:[MessageHandler(Filters.text,
                                                set_pet_name)
            ],
            CASE_MEDICINE:[CommandHandler('done',
                                            create_new_case),
                            MessageHandler(Filters.text,
                                            add_case_medicine)
            ],
            GET_VISITED_DATE:[MessageHandler(Filters.text,
                                                update_case_date)
            ],
            ADMIN_TIMER:[MessageHandler(Filters.text,
                                         set_reminder_timer)
            ],

            NARROWCAST_TEXT:[MessageHandler(Filters.text, 
                                        narrowcast_text)
            ],

            NARROWCAST:[MessageHandler(Filters.text, 
                                        send_message)
            ],

            BROADCAST:[MessageHandler(Filters.text, 
                                        broadcast_message)
            ]
        },

        fallbacks=[MessageHandler(Filters.regex('^done$'), unknown_command)]
    )

    user_handler = ConversationHandler(
        entry_points = [CommandHandler('user_start', user_start)],

        states= {
            USER_MAIN_MANU: [MessageHandler(Filters.regex('^case$'),
                                            user_add_case)
            ],

            SET_CASE_ID:[MessageHandler(Filters.text,
                                         user_get_case_id)
            ],

        },
        fallbacks=[MessageHandler(Filters.regex('^done$'), unknown_command)]
    )

    dp.add_handler(admin_handler)
    dp.add_handler(user_handler)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()