import os
import time
import textwrap
import telegram.ext
import phonenumbers


from telegram.ext import (
    Updater,
    Filters,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
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
    show_freelancer_orders,
    show_customer_start,
    show_creating_order_step,
    show_customer_step,
    show_customer_orders,
    show_freelancers,
    show_freelancer_menu,
    show_order_detail
)
from pprint import pprint


def get_user(func):
    def wrapper(update, context):
        chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id
        bot_state, _ = BotState.objects.get_or_create(telegram_id=chat_id)
        context.user_data['bot_state'] = bot_state
        return func(update, context)
    return wrapper


class TgDialogBot:

    def __init__(self, tg_token, states_functions):
        self.tg_token = tg_token
        self.states_functions = states_functions
        self.updater = Updater(token=tg_token, use_context=True)
        self.updater.dispatcher.add_handler(PreCheckoutQueryHandler(get_user(self.handle_users_reply)))
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
        elif update.pre_checkout_query:
            user_reply = ''
            chat_id = update.effective_user.id
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
            name_data = user_data['full_name'].split()
            first_name = name_data[0].strip()
            last_name = name_data[1].strip() if len(name_data) > 1 else 'Нет данных'
            freelancer.username = f'{update.effective_user.username}_{chat_id}'
            freelancer.phone_number = user_data['phone_number']
            freelancer.first_name = first_name
            freelancer.last_name = last_name
            freelancer.telegram_id = update.effective_user.id
            freelancer.save()
            show_freelancer_menu(context, chat_id)
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
            context.user_data['full_name'] = update.message.text
            return 'HANDLE_AUTH'


def handle_freelancer(update, context):
    chat_id = update.effective_chat.id
    user_data = context.user_data
    if update.callback_query and update.callback_query.data == 'free_orders':
        show_freelancer_orders(context, chat_id)
    elif update.callback_query and update.callback_query.data == 'my_orders':
        show_freelancer_orders(context, chat_id, freelancer_orders=True)
    elif update.callback_query and update.callback_query.data.split(':')[0] == 'detail':
        order_pk = update.callback_query.data.split(':')[1]
        show_order_detail(context, chat_id, order_pk)
    elif update.callback_query and update.callback_query.data == 'break':
        show_freelancer_menu(context, chat_id)
    elif update.callback_query and update.callback_query.data.split(':')[0] == 'choice':
        order_pk = update.callback_query.data.split(':')[1]
        order = Order.objects.get(pk=order_pk)
        freelancer = Freelancer.objects.get(telegram_id=chat_id)
        order.freelancer = freelancer
        order.status = '2 selected'
        order.save()
    elif update.callback_query and update.callback_query.data.split(':')[0] == 'answer':
        user_data['customer_telegram_id'] = update.callback_query.data.split(':')[1]
        order_pk = update.callback_query.data.split(':')[2]
        user_data['message_for_order'] = order_pk
        text = 'Введите сообщение для отправки заказчику'
        context.bot.send_message(chat_id, text=text)
    elif user_data.get('customer_telegram_id'):
        user_data = context.user_data
        message = update.message.text
        order_pk = user_data['message_for_order']
        order = Order.objects.get(pk=order_pk)
        text = textwrap.dedent(
            f'''
            Сообщение от фрилансера по заказу №{order_pk}
            Название: {order.title}
            Сообщение: "{message}"
            '''
        )
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton('Ответить фрилансеру', callback_data=f'answer:{chat_id}:{order_pk}')]],
            resize_keyboard=True
        )
        context.bot.send_message(chat_id=user_data['customer_telegram_id'], text=text, reply_markup=reply_markup)
        text = 'Ваше сообщение отправлено'
        context.bot.send_message(chat_id=chat_id, text=text)
        show_freelancer_menu(context, chat_id)
        del user_data['customer_telegram_id']
        del user_data['message_for_order']

    return 'HANDLE_FREELANCER'


def handle_customer(update, context):
    chat_id = update.effective_chat.id
    user_data = context.user_data
    customer = Customer.objects.filter(username=f'{update.effective_user.username}_{chat_id}')
    if (
            update.callback_query and
            update.callback_query.data in ['economy', 'base', 'vip'] and
            user_data.get('callback_previous') != 'pay'
    ):
        user_reply = update.callback_query.data
        value = {'economy': 500, 'base': 1000, 'vip': 3000}
        user_data['total_value'] = value[user_reply]
        Freelancer.objects.filter(
            username=f'{update.effective_user.username}_{chat_id}'
        ).delete()
        customer, _ = Customer.objects.get_or_create(
            username=f'{update.effective_user.username}_{chat_id}',
        )
        name_data = user_data['full_name'].split()
        first_name = user_data['full_name'].split()[0].strip()
        last_name = user_data['full_name'].split()[1].strip() if len(name_data) > 1 else 'Нет данных'
        customer.status = user_reply
        customer.phone_number = user_data['phone_number']
        customer.first_name = first_name
        customer.last_name = last_name
        customer.telegram_id = update.effective_user.id
        customer.save()
        show_customer_step(context, chat_id)
        return 'HANDLE_CUSTOMER'
    elif (
            customer and not customer[0].payment_status and
            update.callback_query.data != 'pay' and
            update.callback_query.data not in ['economy', 'base', 'vip']
    ):
        message = 'Чтобы продолжить оплатите тариф'
        context.bot.send_message(chat_id=chat_id, text=message)
        show_customer_step(context, chat_id)
        return 'HANDLE_CUSTOMER'
    elif update.callback_query and update.callback_query.data == 'show_orders':
        show_customer_orders(update, context)
        show_customer_step(context, chat_id)
        return 'HANDLE_CUSTOMER'
    elif update.callback_query and update.callback_query.data == 'create_order':
        user_data['step_order'] = user_data.get('step_order', 0) + 1
        step = user_data['step_order']
        show_creating_order_step(context, chat_id, step)
        return 'CREATE_ORDER'
    elif update.callback_query and update.callback_query.data.split(':')[0] in ['tg_id', 'answer']:
        freelancer_telegram_id = update.callback_query.data.split(':')[1]
        order_pk = update.callback_query.data.split(':')[2]
        user_data['freelancer_telegram_id'] = freelancer_telegram_id
        user_data['message_for_order'] = order_pk
        text = 'Введите сообщение для отправки фрилансеру'
        context.bot.send_message(chat_id=chat_id, text=text)
        return 'HANDLE_CUSTOMER'
    elif user_data.get('freelancer_telegram_id'):
        user_data = context.user_data
        message = update.message.text
        order_pk = user_data['message_for_order']
        order = Order.objects.get(pk=order_pk)
        text = textwrap.dedent(
            f'''
            Сообщение от заказчика по заказу №{order_pk}
            Название: {order.title}
            Сообщение: "{message}"
            '''
        )
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton('Ответить заказчику', callback_data=f'answer:{chat_id}:{order_pk}')]
            ],
            resize_keyboard=True
        )
        context.bot.send_message(chat_id=user_data['freelancer_telegram_id'], text=text, reply_markup=reply_markup)
        text = 'Ваше сообщение отправлено'
        context.bot.send_message(chat_id=chat_id, text=text)
        show_customer_step(context, chat_id)
        del user_data['freelancer_telegram_id']
        del user_data['message_for_order']
        return 'HANDLE_CUSTOMER'
    elif update.callback_query and update.callback_query.data == 'pay':
        show_customer_start(context, chat_id)
        user_data['callback_previous'] = 'pay'
        return 'HANDLE_CUSTOMER'
    elif (
            update.callback_query and
            update.callback_query.data in ['economy', 'base', 'vip'] and
            user_data['callback_previous'] == 'pay'
    ):
        del user_data['callback_previous']
        value = {'economy': 500, 'base': 1000, 'vip': 3000}
        status = update.callback_query.data
        customer = Customer.objects.get(telegram_id=chat_id)
        customer.status = status
        customer.save()
        total_value = value[status]
        context.bot.send_invoice(
            chat_id=update.effective_user.id,
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
    chat_id = update.effective_user.id
    customer = Customer.objects.get(username=f'{update.effective_user.username}_{chat_id}')
    if query.invoice_payload != 'Custom-Payload':
        context.bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=False,
            error_message="Something went wrong...")
    else:
        context.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
        show_customer_step(context, chat_id)
        customer.payment_status = True
        customer.save()

    return 'HANDLE_CUSTOMER'


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
        del user_data['step_order']
        customer, _ = Customer.objects.get_or_create(
            username=f'{update.effective_user.username}_{chat_id}',
        )
        if update.callback_query and update.callback_query.data != 'break':
            order = Order.objects.create(
                client=customer,
                title=user_data['order_title'],
                description=user_data['order_description']
            )
            show_order_detail(context, chat_id, order.pk, button=False)
        show_customer_step(context, chat_id)
        return 'HANDLE_CUSTOMER'
    show_creating_order_step(context, chat_id, step)

    return 'CREATE_ORDER'
