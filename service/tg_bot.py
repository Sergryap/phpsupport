import os
import time
import textwrap
import telegram.ext


from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    PollAnswerHandler,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    )

from telegram import Update
from django.contrib.auth.models import User

from service.models import Profile


def get_user(func):
    def wrapper(update, context):
        chat_id = update.message.chat_id
        user, _ = Profile.objects.get_or_create(telegram_id=chat_id)
        context.user_data['user'] = user
        return func(update, context)
    return wrapper


class TgDialogBot:

    def __init__(self, tg_token, states_functions):
        self.tg_token = tg_token
        self.states_functions = states_functions
        self.updater = Updater(token=tg_token, use_context=True)
        self.updater.dispatcher.add_handler(CommandHandler('start', get_user(self.handle_users_reply)))

    def handle_users_reply(self, update, context):
        user = context.user_data['user']
        if update.message:
            user_reply = update.message.text
            chat_id = update.message.chat_id
        elif update.callback_query:
            user_reply = update.callback_query.data
            chat_id = update.callback_query.message.chat_id
        elif update.poll_answer:
            user_reply = update.poll_answer.option_ids
            chat_id = update.poll_answer.user.id
        else:
            return

        if user_reply == '/start':
            user_state = 'START'

        else:
            user_state = user.bot_state
            user_state = user_state if user_state else 'HANDLE_AUTH'

        state_handler = self.states_functions[user_state]
        next_state = state_handler(update, context)
        user.bot_state = next_state


def start(update: Update, context: CallbackContext):
    login_user = update.effective_user.username
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.effective_message.text,
    )

    return "START"
