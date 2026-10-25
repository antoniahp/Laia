from domain.exceptions import MessageNotSent


class HandleTelegramMessageCommand:
    """Mensajes que escriben al bot: /start para unir la cuenta, o la respuesta a una duda de Laia."""

    def __init__(self, repositories, message_service, live_calls):
        self.repositories = repositories
        self.message_service = message_service
        self.live_calls = live_calls

    def execute(self, dto):
        text = (dto.text or "").strip()
        if text.startswith("/start"):
            return self._link(dto.chat_id, text.split(maxsplit=1)[1] if " " in text else "")

        account = self.repositories.accounts.find_by_telegram_chat(dto.chat_id)
        if not account:
            return self._reply(dto.chat_id, "No sé quién eres. Conéctame desde la app con «Conectar Telegram».")
        call = self.live_calls.waiting_for(account.id)
        if call and call.answer(text):
            self._reply(dto.chat_id, "👍 Se lo digo.")
        else:
            self._reply(dto.chat_id, "Ahora no tengo ninguna duda pendiente. Para pedir algo, usa la app.")

    def _link(self, chat_id, code):
        account = self.repositories.accounts.find_by_link_code(code) if code else None
        if not account:
            return self._reply(chat_id, "Hola, soy Laia. Para conectarme, pulsa «Conectar Telegram» en la app.")
        self.repositories.accounts.unlink_telegram_chat(chat_id)
        account.link_telegram(chat_id)
        self.repositories.accounts.save(account, ["telegram_chat_id", "telegram_link_code"])
        for call in self.live_calls.for_account(account.id):
            call.telegram_chat_id = chat_id
        self._reply(chat_id, f"¡Conectado, {account.name or account.email}! Aquí te avisaré y te preguntaré cuando dude.")

    def _reply(self, chat_id, text):
        try:
            self.message_service.send(chat_id, text)
        except MessageNotSent:
            pass
