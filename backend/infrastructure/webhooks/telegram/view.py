"""Mensajes y botones que llegan al bot de Telegram."""

import hmac
import json
import logging

from django.conf import settings
from ninja import Router
from ninja.errors import HttpError

from application.commands.handle_telegram_button.command import HandleTelegramButtonCommand
from application.commands.handle_telegram_button.command_dto import HandleTelegramButtonCommandDTO
from application.commands.handle_telegram_message.command import HandleTelegramMessageCommand
from application.commands.handle_telegram_message.command_dto import HandleTelegramMessageCommandDTO
from infrastructure import dependencies

logger = logging.getLogger(__name__)
router = Router(tags=["webhooks"])


@router.post("/telegram/webhook")
def telegram_webhook(request):
    secret = settings.LAIA["TELEGRAM_WEBHOOK_SECRET"]
    received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret and not hmac.compare_digest(received, secret):
        raise HttpError(403, "No autorizado")

    update = json.loads(request.body or b"{}")
    args = (dependencies.get_repositories(), dependencies.get_message_service(), dependencies.get_live_calls())
    try:
        if "callback_query" in update:
            button = update["callback_query"]
            message = button.get("message", {})
            HandleTelegramButtonCommand(*args).execute(
                HandleTelegramButtonCommandDTO(
                    chat_id=message.get("chat", {}).get("id"),
                    message_id=message.get("message_id"),
                    callback_id=button.get("id", ""),
                    data=button.get("data", ""),
                )
            )
        elif "message" in update and update["message"].get("text"):
            message = update["message"]
            HandleTelegramMessageCommand(*args).execute(
                HandleTelegramMessageCommandDTO(chat_id=message["chat"]["id"], text=message["text"])
            )
    except Exception:  # Telegram reintenta si respondemos con error: mejor registrar y contestar 200
        logger.exception("Error procesando un mensaje de Telegram")
    return {}
