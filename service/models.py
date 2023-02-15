from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField


class Profile(models.Model):
    status_choices = [
        ('not processed', 'Не обработан'),
        ('Customer', 'Заказчик'),
        ('Freelancer', 'Фрилансер'),
        ('Admin', 'Администратор'),
    ]
    phone_number = PhoneNumberField(
        verbose_name='Телефон',
        db_index=True,
        region='RU',
        unique=True,
        blank=True,
        null=True
    )
    telegram_id = models.IntegerField(
        'Telegram Id',
        db_index=True,
        blank=True,
        null=True
    )
    status = models.CharField(
        verbose_name='Статус',
        choices=status_choices,
        default='not processed',
        db_index=True,
        max_length=30,
    )
    bot_state = models.CharField(
        'Текущее состояния бота',
        max_length=100,
        blank=True,
        help_text="Стейт машина бота"
    )
    full_name = models.CharField(
        'Полное имя',
        max_length=200,
        blank=True,
    )


class Order(models.Model):
    status_choices = [
        ('1 not processed', 'Необработан'),
        ('2 selected', 'Выбран фрилансер'),
        ('3 performed', 'В работе'),
        ('4 completed', 'Выполнен'),
        ('5 expired', 'Просрочен')
    ]
    client = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='client_orders',
        verbose_name='Клиент',
    )
    freelancer = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='freelancer_orders',
        verbose_name='Фрилансер',
    )
    description = models.TextField(
        verbose_name='Описание заказа',
        max_length=100,
        null=True,
        blank=True
    )
    status = models.CharField(
        verbose_name='Статус',
        choices=status_choices,
        default='1 not processed',
        db_index=True,
        max_length=30,
    )
    created_at = models.DateTimeField(
        verbose_name='Время создания',
        default=timezone.now()
    )
    deadline = models.DateTimeField(
        verbose_name='Срок выполнения',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.client}_{self.freelancer}_{self.created_at}'
