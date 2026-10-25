import hmac

from django.conf import settings
from django.utils import timezone

from domain.entities import Account
from domain.exceptions import EmailAlreadyUsed, TermsNotAccepted, WrongSignupCode


class RegisterAccountCommand:
    """Crea una cuenta y devuelve su token de sesión. Si el email es ADMIN_EMAIL, será administradora."""

    def __init__(self, repositories, token_service):
        self.repositories = repositories
        self.token_service = token_service

    def execute(self, dto):
        if not dto.accept_terms:
            raise TermsNotAccepted()
        email = Account.normalize_email(dto.email)
        signup_code = settings.LAIA["SIGNUP_CODE"]
        if signup_code and not hmac.compare_digest(dto.signup_code.strip(), signup_code):
            raise WrongSignupCode()
        if self.repositories.accounts.find_by_email(email):
            raise EmailAlreadyUsed()
        account = Account(email=email, name=dto.name.strip())
        account.set_password(dto.password)
        account.accept_terms(settings.LAIA["TERMS_VERSION"], timezone.now())
        admin_email = settings.LAIA["ADMIN_EMAIL"]
        account.is_admin = bool(admin_email) and email == admin_email
        self.repositories.accounts.save(account)
        return self.token_service.issue(account.id)
