import pytest

from application.shared.live_calls import LiveCallRegistry
from domain.entities import Account, Business
from infrastructure.repositories.django_repositories import build_django_repositories
from infrastructure.services.jwt_token_service import JwtTokenService
from tests.fakes import FakeCallService, FakeMessageService


@pytest.fixture(autouse=True)
def test_settings(settings):
    settings.LAIA = {
        **settings.LAIA,
        "ADMIN_EMAIL": "admin@laia.dev",
        "SIGNUP_CODE": "",
        "MAX_CALLS_PER_DAY": 2,
        "ALLOWED_COUNTRIES": ["ES", "DE"],
        "PUBLIC_URL": "https://laia.example",
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_BOT_USERNAME": "laia_bot",
        "TELEGRAM_WEBHOOK_SECRET": "secreto",
        "GOOGLE_PLACES_API_KEY": "",
    }
    return settings


@pytest.fixture
def repositories(db):
    return build_django_repositories()


@pytest.fixture
def token_service():
    return JwtTokenService()


@pytest.fixture
def message_service():
    return FakeMessageService()


@pytest.fixture
def call_service():
    return FakeCallService()


@pytest.fixture
def live_calls():
    return LiveCallRegistry()


@pytest.fixture
def account(db):
    account = Account(email="marta@laia.dev", name="Marta", address="Calle Mayor 12, Madrid", telegram_chat_id=222)
    account.set_password("12345678")
    account.save()
    return account


@pytest.fixture
def admin(db):
    admin = Account(email="admin@laia.dev", name="Toni", is_admin=True, telegram_chat_id=111)
    admin.set_password("12345678")
    admin.save()
    return admin


@pytest.fixture
def pizzeria(db):
    return Business.objects.create(name="Tres Hermanas", phone="+34612345678", country="ES", language="es", status=Business.VERIFIED)
