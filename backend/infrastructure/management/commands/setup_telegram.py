from django.conf import settings
from django.core.management.base import BaseCommand

from domain.exceptions import MessageNotSent
from infrastructure.services.telegram_message_service import TelegramMessageService


class Command(BaseCommand):
    help = "Registra el webhook del bot de Telegram en PUBLIC_URL/telegram/webhook."

    def handle(self, *args, **options):
        cfg = settings.LAIA
        service = TelegramMessageService()
        if not service.is_enabled():
            self.stdout.write("Telegram desactivado (falta TELEGRAM_BOT_TOKEN).")
            return
        if not cfg["PUBLIC_URL"]:
            self.stdout.write(self.style.WARNING("Falta PUBLIC_URL: no puedo registrar el webhook."))
            return
        try:
            me = service.call("getMe")
            service.call(
                "setWebhook",
                url=f"{cfg['PUBLIC_URL']}/telegram/webhook",
                secret_token=cfg["TELEGRAM_WEBHOOK_SECRET"] or None,
                allowed_updates=["message", "callback_query"],
            )
        except MessageNotSent as error:
            self.stdout.write(self.style.ERROR(f"Telegram no acepta la configuración: {error}"))
            return
        username = me.get("username")
        self.stdout.write(self.style.SUCCESS(f"Telegram listo: @{username}"))
        if username and username != cfg["TELEGRAM_BOT_USERNAME"]:
            self.stdout.write(self.style.WARNING(f"Pon TELEGRAM_BOT_USERNAME={username} en tu configuración."))
