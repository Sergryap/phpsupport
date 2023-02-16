from django.conf import settings
from django.core.management import BaseCommand

from service.tg_bot import (
    TgDialogBot,
    start,
    handle_auth,
    handle_customer,
    precheckout_callback,
    create_order
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            start_bot()
        except Exception as exc:
            print(exc)
            raise


def start_bot():

    bot = TgDialogBot(
        settings.TELEGRAM_TOKEN,
        {
            'START': start,
            'HANDLE_AUTH': handle_auth,
            'HANDLE_CUSTOMER': handle_customer,
            'PRECHECKOUT': precheckout_callback,
            'CREATE_ORDER': create_order

        }
    )
    bot.updater.start_polling()
    bot.updater.idle()  # required in detached mode on server
