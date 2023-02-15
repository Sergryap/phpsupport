# Generated by Django 4.1.7 on 2023-02-15 09:59

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0008_profile_full_name_alter_order_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_orders', to='service.profile', verbose_name='Клиент'),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 15, 9, 59, 16, 952605, tzinfo=datetime.timezone.utc), verbose_name='Время создания'),
        ),
        migrations.AlterField(
            model_name='order',
            name='freelancer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='freelancer_orders', to='service.profile', verbose_name='Фрилансер'),
        ),
    ]