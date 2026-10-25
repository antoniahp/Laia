from domain.exceptions import CallInProgressCannotDelete, SessionExpired


class DeleteAccountCommand:
    """Derecho de supresión: borra la cuenta y todos sus pedidos y conversaciones."""

    def __init__(self, repositories, live_calls):
        self.repositories = repositories
        self.live_calls = live_calls

    def execute(self, dto):
        account = self.repositories.accounts.find(dto.account_id)
        if not account:
            raise SessionExpired()
        if self.live_calls.has_active_call(account.id):
            raise CallInProgressCannotDelete()
        self.repositories.accounts.delete(account)
