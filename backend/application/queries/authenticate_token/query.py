class AuthenticateTokenQuery:
    """Devuelve la cuenta del token, o None si no vale."""

    def __init__(self, repositories, token_service):
        self.repositories = repositories
        self.token_service = token_service

    def execute(self, dto):
        account_id = self.token_service.read(dto.token)
        return self.repositories.accounts.find(account_id) if account_id else None
