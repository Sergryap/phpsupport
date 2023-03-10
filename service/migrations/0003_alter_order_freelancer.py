# Generated by Django 4.1.7 on 2023-02-16 16:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_customer_status'),
        ('service', '0002_order_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='freelancer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='freelancer_orders', to='users.freelancer', verbose_name='Фрилансер'),
        ),
    ]
