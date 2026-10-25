from domain.exceptions import SessionExpired, TelegramNotConfigured


class CreateTelegramLinkCommand:
    """Genera un enlace de un solo uso para unir el chat de Telegram con la cuenta."""

    def __init__(self, repositories, message_service):
        self.repositories = repositories
        self.message_service = message_service

    def execute(self, dto):
        if not self.message_service.is_enabled():
            raise TelegramNotConfigured()
        account = self.repositories.accounts.find(dto.account_id)
        if not account:
            raise SessionExpired()
        code = account.renew_link_code()
        self.repositories.accounts.save(account, ["telegram_link_code"])
        url = self.message_service.link_url(code)
        if not url:
            raise TelegramNotConfigured("El bot de Telegram no responde ahora mismo.")
        return url
