from domain.exceptions import WrongCredentials


class LogInCommand:
    def __init__(self, repositories, token_service):
        self.repositories = repositories
        self.token_service = token_service

    def execute(self, dto):
        account = self.repositories.accounts.find_by_email((dto.email or "").strip().lower())
        if not account or not account.check_password(dto.password):
            raise WrongCredentials()
        return self.token_service.issue(account.id)
