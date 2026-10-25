from application.commands.review_business.command import ReviewBusinessCommand
from application.commands.review_business.command_dto import ReviewBusinessCommandDTO
from domain.entities import Business
from domain.exceptions import BusinessNotFound, MessageNotSent


class HandleTelegramButtonCommand:
    """Botones de Telegram: responder Sí/No a Laia (a|pedido|respuesta) o revisar un negocio (b|negocio|ok|no)."""

    def __init__(self, repositories, message_service, live_calls):
        self.repositories = repositories
        self.message_service = message_service
        self.live_calls = live_calls

    def execute(self, dto):
        account = self.repositories.accounts.find_by_telegram_chat(dto.chat_id)
        if not account:
            return self.message_service.answer_button(dto.callback_id, "No te reconozco")
        parts = (dto.data or "").split("|")

        if len(parts) == 3 and parts[0] == "a":
            call = self.live_calls.get(parts[1])
            if call and call.order.account_id == account.id and call.answer(parts[2]):
                self.message_service.answer_button(dto.callback_id, "Hecho")
                self._close(dto, f"Respondiste: {parts[2]}")
            else:
                self.message_service.answer_button(dto.callback_id, "Esa pregunta ya no está activa")
            return

        if len(parts) == 3 and parts[0] == "b" and account.is_admin:
            status = Business.VERIFIED if parts[2] == "ok" else Business.REJECTED
            try:
                business = ReviewBusinessCommand(self.repositories, self.message_service).execute(
                    ReviewBusinessCommandDTO(admin_id=account.id, business_id=parts[1], status=status)
                )
            except (BusinessNotFound, ValueError):
                return self.message_service.answer_button(dto.callback_id, "No existe")
            self.message_service.answer_button(dto.callback_id, "Guardado")
            self._close(dto, f"{business.name}: {status}")
            return

        self.message_service.answer_button(dto.callback_id)

    def _close(self, dto, note):
        try:
            self.message_service.remove_buttons(dto.chat_id, dto.message_id)
            self.message_service.send(dto.chat_id, note)
        except MessageNotSent:
            pass
