import os
import time
import textwrap
import telegram.ext
import phonenumbers


from telegram.ext import (
    Updater,
    Filters,
    CallbackQueryHandler,
    PollAnswerHandler,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    )

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from service.models import Profile
from service.tg_lib import show_auth_keyboard, show_send_contact_keyboard


def get_user(func):
    def wrapper(update, context):
        chat_id = update.effective_chat.id
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
        self.updater.dispatcher.add_handler(CallbackQueryHandler(get_user(self.handle_users_reply)))
        self.updater.dispatcher.add_handler(
            MessageHandler(Filters.text | Filters.contact, get_user(self.handle_users_reply))
        )

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
        user.save()


def start(update, context):
    chat_id = update.message.chat_id
    show_auth_keyboard(context, chat_id)
    return 'HANDLE_AUTH'


def handle_auth(update, context):
    user = context.user_data['user']
    if update.callback_query:
        user.status = update.callback_query.data
        user.save()
        return 'HANDLE_AUTH'
    if not update.message:
        return 'HANDLE_AUTH'
    chat_id = update.message.chat_id
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        if phone_number and phonenumbers.is_valid_number(phonenumbers.parse(phone_number, 'RU')):
            user.phone_number = phone_number
            user.save()
            context.bot.send_message(
                chat_id=chat_id,
                text=f'Введите Ваше Имя и Фамилию:',
                reply_markup=telegram.ReplyKeyboardRemove()
                )
            return 'HANDLE_AUTH'
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text='Вы ввели неверный номер телефона. Попробуйте еще раз:'
                )
            return 'HANDLE_AUTH'
    elif update.message.text:
        if 'Авторизоваться' in update.message.text:
            show_send_contact_keyboard(context, chat_id)
            context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
            return 'HANDLE_AUTH'
        else:
            user.full_name = update.message.text
            user.save()
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Выберите, кем вы являетесь:',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton('Заказчик', callback_data='Customer'),
                            InlineKeyboardButton('Фрилансер', callback_data='Freelancer')
                        ]
                    ],
                    resize_keyboard=True
                )
            )
            return 'HANDLE_AUTH'
