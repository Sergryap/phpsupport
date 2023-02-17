import re
import json
import textwrap

import telegram.ext

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

from django.utils.timezone import now
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from django.conf import settings
from users.models import Customer, Freelancer
from service.models import Order


def show_auth_user_type(context, chat_id):
    message = 'Перед началом использования представьтесь кем вы являетесь'
    context.bot.send_message(
        chat_id=chat_id,
        text=message,
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


def show_auth_keyboard(context, chat_id):
    message = textwrap.dedent('''
        Перед началом использования необходимо отправить номер телефона.
        Пожалуйста, нажмите на кнопку Авторизоваться ниже:''')
    auth_keyboard = KeyboardButton(text="🔐 Авторизоваться")
    reply_markup = ReplyKeyboardMarkup(
        [[auth_keyboard]], one_time_keyboard=False,
        row_width=1, resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_send_contact_keyboard(context, chat_id):
    message = '''Продолжая регистрацию вы соглашаетесь с политикой конфиденциальности'''
    contact_keyboard = KeyboardButton(text="☎ Передать контакт", request_contact=True)
    reply_markup = ReplyKeyboardMarkup(
        [[contact_keyboard]], one_time_keyboard=False,
        row_width=1, resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_freelancer_start(context, chat_id):
    message = 'Подайте заявку на участие в одном из заказов:'
    orders = Order.objects.filter(status='1 not processed')
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(order.title, callback_data=order.title)] for order in orders
        ],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_customer_start(context, chat_id):
    message = 'Выберите тариф:'
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Эконом', callback_data='economy'),
                InlineKeyboardButton('Стандарт', callback_data='base'),
                InlineKeyboardButton('VIP', callback_data='vip'),
            ]
        ],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_creating_order_step(context, chat_id, step):
    message = {
        1: 'Введите краткое название заказа',
        2: 'Введите подробное описание заказа',
        3: 'Выберите исполнителя, либо пропустите данный пункт',
        4: 'Нажмите чтобы посмотреть весь заказа'
    }
    callback_data = {
        1: 'title',
        2: 'description',
        3: 'freelancer',
        4: 'verify'
    }
    reply_markup = {
        1: InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton('Отправить', callback_data=callback_data[step])]],
            resize_keyboard=True
        ),
        2: InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton('Отправить', callback_data=callback_data[step])]],
            resize_keyboard=True
        ),
        3: InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton('Freelancer', callback_data=callback_data[step]),
                    InlineKeyboardButton('Пропустить', callback_data='break')
                ],
            ],
            resize_keyboard=True
        ),
        4: InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton('Весь заказ', callback_data=callback_data[step])]],
            resize_keyboard=True
        ),
    }

    context.bot.send_message(chat_id=chat_id, text=message[step], reply_markup=reply_markup[step])


def show_customer_step(context, chat_id):
    message = 'Выберите дальнейшее действие:'
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton('Оплатить тариф', callback_data='pay')],
            [InlineKeyboardButton('Создать заказ', callback_data='create_order')],
            [InlineKeyboardButton('Посмотреть свои заказы', callback_data='show_orders')],
        ],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_customer_orders(update, context):
    user_data = context.user_data
    chat_id = update.effective_chat.id
    customer, _ = Customer.objects.get_or_create(
        username=f'{update.effective_user.username}_{chat_id}',
    )
    orders = Order.objects.filter(client=customer)
    for order in orders:
        status = order.status
        if status == '33' or status == '1 not processed':
            freelancer = 'Не выбран'
            callback_data = 'empty_telegramm_id'
            reply_markup = None
        else:
            freelancer = f'{order.freelancer.first_name}'
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            'Написать фрилансеру',
                            callback_data=f"tg_id:{order.freelancer.telegram_id}"
                        )
                    ]
                ],
                resize_keyboard=True
            )

        context.bot.send_message(
            chat_id=chat_id,
            text='\n'.join(
                [
                    f"Название: {order.title}",
                    f"Описание: {order.description}",
                    f"Фрилансер: {freelancer}"
                ],
            ),
            reply_markup=reply_markup
        )


def show_freelancers(context, chat_id):
    freelancers = Freelancer.objects.all()
    inline_keyboard = [[
            InlineKeyboardButton('Пропустить', callback_data='break')
        ]]
    for freelancer in freelancers:
        inline_keyboard.append([
            InlineKeyboardButton(freelancer.first_name, callback_data=freelancer.telegram_id)
        ])
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard,
        resize_keyboard=True
    )
    text = 'Выберите исполнителя для подробной информации, либо пропустите'
    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


