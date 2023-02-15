from django.conf import settings
from django.core.management import BaseCommand

from service.tg_bot import (
    TgDialogBot,
    start,
    handle_auth,
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
        settings.TELEGRAM_ACCESS_TOKEN,
        {
            'START': start,
            'HANDLE_AUTH': handle_auth,
            # 'HANDLE_SELECTIONS': handle_select,

        }
    )
    bot.application.run_polling()
    bot.application.idle()  # required in detached mode on server
