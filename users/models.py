from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MaxValueValidator


class User(AbstractUser):
    telegram_id = models.IntegerField(
        'Telegram Id',
        null=True,
        blank=True
    )
    phone_number = PhoneNumberField(
        verbose_name='Телефон',
        region='RU',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class Customer(User):
    status_choices = [
        ('no status', 'Нет подписки'),
        ('economy', 'Эконом'),
        ('base', 'Базовый'),
        ('vip', 'VIP'),
    ]

    status = models.CharField(
        verbose_name='Статус',
        choices=status_choices,
        default='not processed',
        db_index=True,
        max_length=30,
    )

    class Meta:
        verbose_name = 'Заказчик'
        verbose_name_plural = 'Заказчики'

class Freelancer(User):
    rating = models.IntegerField(
        'Рейтинг',
        validators=[MaxValueValidator(100),],
        default=100
    )

    class Meta:
        verbose_name = 'Фрилансер'
        verbose_name_plural = 'Фрилансеры'