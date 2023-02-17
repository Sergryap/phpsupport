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

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from users.models import User, Freelancer, Customer, BotState
from service.models import Order
from service.tg_lib import (
    show_auth_keyboard,
    show_send_contact_keyboard,
    show_auth_user_type,
    show_freelancer_start,
    show_customer_start,
    show_creating_order_step,
    show_customer_step,
    show_customer_orders
)
from pprint import pprint


def get_user(func):
    def wrapper(update, context):
        chat_id = update.effective_chat.id
        bot_state, _ = BotState.objects.get_or_create(telegram_id=chat_id)
        context.user_data['bot_state'] = bot_state
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
        bot_state = context.user_data['bot_state']
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
            context.user_data.update({'chat_id': chat_id, 'full_name': '', 'phone_number': ''})
        else:
            user_state = bot_state.bot_state
            user_state = user_state if user_state else 'HANDLE_AUTH'

        state_handler = self.states_functions[user_state]
        next_state = state_handler(update, context)
        bot_state.bot_state = next_state
        bot_state.save()


def start(update, context):
    chat_id = update.message.chat_id
    show_auth_keyboard(context, chat_id)
    return 'HANDLE_AUTH'


def handle_auth(update, context):
    chat_id = update.effective_chat.id
    if update.callback_query:
        status = update.callback_query.data
        if status == 'Freelancer':
            context.user_data['status'] = 'Freelancer'
            user_data = context.user_data
            Customer.objects.filter(
                username=f'{update.effective_user.username}_{chat_id}'
            ).delete()
            freelancer, _ = Freelancer.objects.get_or_create(
                username=f'{update.effective_user.username}_{chat_id}',
            )
            freelancer.username = f'{update.effective_user.username}_{chat_id}'
            freelancer.phone_number = user_data['phone_number']
            freelancer.first_name = update.effective_user.first_name 
            freelancer.last_name = update.effective_user.last_name
            freelancer.telegram_id = update.effective_user.id
            freelancer.save()
            show_freelancer_start(context, chat_id)
            return 'HANDLE_FREELANCER'
        elif status == 'Customer':
            context.user_data['status'] = 'Customer'
            show_customer_start(context, chat_id)
            return 'HANDLE_CUSTOMER'
    if not update.message:
        return 'HANDLE_AUTH'
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        if phone_number and phonenumbers.is_valid_number(phonenumbers.parse(phone_number, 'RU')):
            context.user_data['phone_number'] = phone_number
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
            show_auth_user_type(context, chat_id)
            context.user_data['phone_number'] = update.message.text
            return 'HANDLE_AUTH'


def handle_customer(update, context):
    chat_id = update.effective_chat.id
    user_data = context.user_data
    if update.callback_query and update.callback_query.data in ['economy', 'base', 'vip']:
        user_reply = update.callback_query.data
        value = {'economy': 500, 'base': 1000, 'vip': 3000}
        user_data['total_value'] = value[user_reply]

        phone_number = user_data['phone_number']
        Freelancer.objects.filter(
            username=f'{update.effective_user.username}_{chat_id}'
        ).delete()
        customer, _ = Customer.objects.get_or_create(
            username=f'{update.effective_user.username}_{chat_id}',
        )
        customer.status = user_reply
        customer.phone_number = phone_number
        customer.first_name = update.effective_user.first_name
        customer.last_name = update.effective_user.last_name
        customer.telegram_id = update.effective_user.id
        customer.save()
        show_customer_step(context, chat_id)
        return 'HANDLE_CUSTOMER'
    elif update.callback_query and update.callback_query.data == 'show_orders':
        show_customer_orders(update, context)
        show_customer_step(context, chat_id)
        return 'HANDLE_CUSTOMER'
    elif update.callback_query and update.callback_query.data == 'create_order':
        return create_order(update, context)

    elif update.callback_query and update.callback_query.data == 'pay':
        total_value = user_data['total_value']
        context.bot.send_invoice(
            chat_id=chat_id,
            title='Оплата заказа в php_support',
            description='Payment Example using python-telegram-bot',
            payload='Custom-Payload',
            provider_token=os.environ['PROVIDER_TOKEN'],
            currency='RUB',
            prices=[LabeledPrice('Test', total_value * 100)]
        )
        return 'PRECHECKOUT'


def precheckout_callback(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        context.bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=False,
            error_message="Something went wrong...")
    else:
        context.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    # context.bot.send_message(
    #     chat_id=update.effective_user.id,
    #     text='Хотите продолжить?',
    #     reply_markup=btn.get_restart_button()
    # )
        return 'CREATE_ORDER'


def create_order(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_data = context.user_data
    user_data['step_order'] = user_data.get('step_order', 0) + 1
    step = user_data['step_order']
    if step == 2:
        user_data['order_title'] = update.message.text
    elif step == 3:
        user_data['order_description'] = update.message.text
    elif step == 4:
        user_data['step_order'] = 0
        customer, _ = Customer.objects.get_or_create(
            username=f'{update.effective_user.username}_{chat_id}',
        )
        order = Order.objects.create(
            client=customer,
            title=user_data['order_title'],
            description=user_data['order_description']
        )
        context.bot.send_message(
            chat_id=chat_id,
            text='\n'.join(
                [
                    f"Название: {user_data['order_title']}",
                    f"Описание: {user_data['order_description']}"
                ]
            )
        )
        show_customer_step(context, chat_id)
        return 'HANDLE_CUSTOMER'
    show_creating_order_step(context, chat_id, step)

    return 'CREATE_ORDER'
