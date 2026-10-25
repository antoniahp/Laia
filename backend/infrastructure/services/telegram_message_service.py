import logging

import httpx
from django.conf import settings

from domain.exceptions import MessageNotSent
from domain.services.message_service import MessageService

logger = logging.getLogger(__name__)


class TelegramMessageService(MessageService):
    """Bot API de Telegram, sin librerías extra."""

    def __init__(self):
        self.token = settings.LAIA["TELEGRAM_BOT_TOKEN"]
        self.username = settings.LAIA["TELEGRAM_BOT_USERNAME"]

    def is_enabled(self):
        return bool(self.token)

    def call(self, method, **params):
        if not self.token:
            raise MessageNotSent("Telegram no está configurado")
        try:
            response = httpx.post(f"https://api.telegram.org/bot{self.token}/{method}", json=params, timeout=15)
            data = response.json()
        except Exception as error:  # noqa: BLE001
            raise MessageNotSent(str(error)) from error
        if not data.get("ok"):
            raise MessageNotSent(data.get("description", "error de Telegram"))
        return data.get("result")

    def send(self, chat_id, text, buttons=None):
        params = {"chat_id": chat_id, "text": text}
        if buttons:
            params["reply_markup"] = {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in buttons]}
        result = self.call("sendMessage", **params)
        return str(result.get("message_id", "")) if isinstance(result, dict) else ""

    def answer_button(self, callback_id, text=""):
        try:
            self.call("answerCallbackQuery", callback_query_id=callback_id, text=text)
        except MessageNotSent as error:
            logger.warning("Telegram answerCallbackQuery: %s", error)

    def remove_buttons(self, chat_id, message_id):
        self.call("editMessageReplyMarkup", chat_id=chat_id, message_id=message_id, reply_markup={"inline_keyboard": []})

    def link_url(self, link_code):
        return f"https://t.me/{self.username}?start={link_code}" if self.username else None
