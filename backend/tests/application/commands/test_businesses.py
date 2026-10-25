import pytest

from application.commands.propose_business.command import ProposeBusinessCommand
from application.commands.propose_business.command_dto import ProposeBusinessCommandDTO
from application.commands.review_business.command import ReviewBusinessCommand
from application.commands.review_business.command_dto import ReviewBusinessCommandDTO
from domain.entities import Business
from domain.exceptions import BusinessRejected, NotAdmin, PremiumRateNumber
from tests.fakes import FakeVerificationService, google_place


def propose(repositories, message_service, account, verification=None, **data):
    command = ProposeBusinessCommand(repositories, verification or FakeVerificationService(), message_service)
    return command.execute(ProposeBusinessCommandDTO(account_id=account.id, **data))


def test_unknown_business_waits_for_an_admin_on_telegram(repositories, message_service, account, admin):
    business = propose(repositories, message_service, account, name="Radhaus Müller", phone="+49 89 1234567", language="de")
    assert business.status == Business.PENDING
    assert business.country == "DE"
    sent = message_service.sent[0]
    assert sent["chat_id"] == admin.telegram_chat_id
    assert sent["buttons"][0][0][1] == f"b|{business.id}|ok"


def test_google_confirms_the_phone_and_it_is_verified_at_once(repositories, message_service, account):
    business = propose(
        repositories, message_service, account, FakeVerificationService(google_place()), name="Tres Hermanas", phone="612345678"
    )
    assert business.is_verified
    assert business.verified_by == "google_places"
    assert message_service.sent == []


def test_proposing_an_existing_phone_returns_it(repositories, message_service, account, pizzeria):
    assert propose(repositories, message_service, account, name="Otra", phone="+34612345678").id == pizzeria.id


def test_rejected_numbers_cannot_come_back(repositories, message_service, account, pizzeria):
    pizzeria.reject()
    pizzeria.save()
    with pytest.raises(BusinessRejected):
        propose(repositories, message_service, account, name="Otra", phone="+34612345678")


def test_premium_numbers_are_refused(repositories, message_service, account):
    with pytest.raises(PremiumRateNumber):
        propose(repositories, message_service, account, name="Tarot", phone="+34806123456")


def test_admin_review_tells_the_proposer(repositories, message_service, account, admin):
    business = propose(repositories, message_service, account, name="Bar Paco", phone="+34612999888")
    message_service.sent.clear()
    command = ReviewBusinessCommand(repositories, message_service)
    command.execute(ReviewBusinessCommandDTO(admin_id=admin.id, business_id=business.id, status="verificado", ivr_digits="ww1"))
    business.refresh_from_db()
    assert business.is_verified and business.ivr_digits == "ww1"
    assert message_service.sent[0]["chat_id"] == account.telegram_chat_id


def test_only_admins_review(repositories, message_service, account, pizzeria):
    with pytest.raises(NotAdmin):
        ReviewBusinessCommand(repositories, message_service).execute(
            ReviewBusinessCommandDTO(admin_id=account.id, business_id=pizzeria.id, status="rechazado")
        )


def test_admin_proposals_are_verified_at_once(repositories, message_service, admin):
    business = propose(repositories, message_service, admin, name="Pizzería de mi agenda", phone="+34612777888")
    assert business.is_verified and business.verified_by == "admin"
    assert message_service.sent == []
