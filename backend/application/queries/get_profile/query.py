from domain.exceptions import SessionExpired


class GetProfileQuery:
    def __init__(self, repositories):
        self.repositories = repositories

    def execute(self, dto):
        account = self.repositories.accounts.find(dto.account_id)
        if not account:
            raise SessionExpired()
        return account
