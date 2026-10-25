import pytest

from application.commands.create_telegram_link.command import CreateTelegramLinkCommand
from application.commands.create_telegram_link.command_dto import CreateTelegramLinkCommandDTO
from application.commands.log_in.command import LogInCommand
from application.commands.log_in.command_dto import LogInCommandDTO
from application.commands.register_account.command import RegisterAccountCommand
from application.commands.register_account.command_dto import RegisterAccountCommandDTO
from application.commands.update_profile.command import UpdateProfileCommand
from application.commands.update_profile.command_dto import UpdateProfileCommandDTO
from domain.entities import Account
from domain.exceptions import EmailAlreadyUsed, TelegramNotConfigured, TermsNotAccepted, WrongCredentials, WrongSignupCode
from tests.fakes import FakeMessageService


def register(repositories, token_service, **data):
    data.setdefault("accept_terms", True)
    return RegisterAccountCommand(repositories, token_service).execute(RegisterAccountCommandDTO(**data))


def test_register_returns_a_session_and_admin_email_becomes_admin(repositories, token_service):
    token = register(repositories, token_service, email="Admin@Laia.dev", password="12345678")
    account = Account.objects.get(email="admin@laia.dev")
    assert token_service.read(token) == str(account.id)
    assert account.is_admin


def test_duplicated_email(repositories, token_service, account):
    with pytest.raises(EmailAlreadyUsed):
        register(repositories, token_service, email="marta@laia.dev", password="12345678")


def test_signup_code(repositories, token_service, settings):
    settings.LAIA = {**settings.LAIA, "SIGNUP_CODE": "hola123"}
    with pytest.raises(WrongSignupCode):
        register(repositories, token_service, email="x@y.com", password="12345678")
    register(repositories, token_service, email="x@y.com", password="12345678", signup_code="hola123")


def test_log_in(repositories, token_service, account):
    assert LogInCommand(repositories, token_service).execute(LogInCommandDTO(email="MARTA@laia.dev", password="12345678"))
    with pytest.raises(WrongCredentials):
        LogInCommand(repositories, token_service).execute(LogInCommandDTO(email="marta@laia.dev", password="mal"))


def test_update_profile_normalizes_phone(repositories, account):
    UpdateProfileCommand(repositories).execute(UpdateProfileCommandDTO(account_id=account.id, phone="612 000 111", address="Otra 1"))
    account.refresh_from_db()
    assert account.phone == "+34612000111"
    assert account.address == "Otra 1"


def test_telegram_link(repositories, account):
    url = CreateTelegramLinkCommand(repositories, FakeMessageService()).execute(CreateTelegramLinkCommandDTO(account_id=account.id))
    account.refresh_from_db()
    assert url.endswith(account.telegram_link_code)
    with pytest.raises(TelegramNotConfigured):
        CreateTelegramLinkCommand(repositories, FakeMessageService(enabled=False)).execute(
            CreateTelegramLinkCommandDTO(account_id=account.id)
        )


def test_terms_must_be_accepted_and_the_version_is_kept(repositories, token_service):
    with pytest.raises(TermsNotAccepted):
        register(repositories, token_service, email="x@y.com", password="12345678", accept_terms=False)
    register(repositories, token_service, email="x@y.com", password="12345678")
    account = Account.objects.get(email="x@y.com")
    assert account.terms_version == "2026-10" and account.terms_accepted_at is not None
