import config
import telegram.ext
from telegram.ext import Updater
TOKEN=config.BOT_TOEKN

u = Updater(TOKEN, use_context=True)

from telegram.ext import CommandHandler
def callback_alarm(context: telegram.ext.CallbackContext):
    context.bot.send_message(chat_id=context.job.context, text='BEEP')

def callback_timer(update: telegram.Update, context: telegram.ext.CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='Setting a timer for 1 minute!')

    context.job_queue.run_once(callback_alarm, 10, context=update.message.chat_id)

timer_handler = CommandHandler('timer', callback_timer)
u.dispatcher.add_handler(timer_handler)

u.start_polling()
u.idle()