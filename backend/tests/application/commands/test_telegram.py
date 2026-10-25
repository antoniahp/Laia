from application.commands.handle_telegram_button.command import HandleTelegramButtonCommand
from application.commands.handle_telegram_button.command_dto import HandleTelegramButtonCommandDTO
from application.commands.handle_telegram_message.command import HandleTelegramMessageCommand
from application.commands.handle_telegram_message.command_dto import HandleTelegramMessageCommandDTO
from domain.entities import Account, Business


def message(repositories, message_service, live_calls, chat_id, text):
    HandleTelegramMessageCommand(repositories, message_service, live_calls).execute(
        HandleTelegramMessageCommandDTO(chat_id=chat_id, text=text)
    )


def test_start_links_the_chat_and_the_link_only_works_once(repositories, message_service, live_calls, account):
    code = account.telegram_link_code
    message(repositories, message_service, live_calls, 999, f"/start {code}")
    account.refresh_from_db()
    assert account.telegram_chat_id == 999
    assert account.telegram_link_code != code
    assert "Conectado" in message_service.sent[-1]["text"]


def test_a_chat_belongs_to_one_account(repositories, message_service, live_calls, account):
    other = Account(email="otra@b.com")
    other.set_password("12345678")
    other.save()
    message(repositories, message_service, live_calls, account.telegram_chat_id, f"/start {other.telegram_link_code}")
    account.refresh_from_db()
    other.refresh_from_db()
    assert account.telegram_chat_id is None
    assert other.telegram_chat_id == 222


def test_strangers_are_told_how_to_connect(repositories, message_service, live_calls, db):
    message(repositories, message_service, live_calls, 12345, "hola")
    assert "Conectar Telegram" in message_service.sent[-1]["text"]


def test_admin_verifies_from_a_telegram_button(repositories, message_service, live_calls, admin):
    business = Business.objects.create(name="Bar Paco", phone="+34612999888", country="ES")
    HandleTelegramButtonCommand(repositories, message_service, live_calls).execute(
        HandleTelegramButtonCommandDTO(chat_id=admin.telegram_chat_id, message_id=5, callback_id="x", data=f"b|{business.id}|ok")
    )
    business.refresh_from_db()
    assert business.is_verified
    assert message_service.answered_buttons[-1] == "Guardado"


def test_non_admins_cannot_verify(repositories, message_service, live_calls, account):
    business = Business.objects.create(name="Bar Paco", phone="+34612999888", country="ES")
    HandleTelegramButtonCommand(repositories, message_service, live_calls).execute(
        HandleTelegramButtonCommandDTO(chat_id=account.telegram_chat_id, message_id=5, callback_id="x", data=f"b|{business.id}|ok")
    )
    business.refresh_from_db()
    assert business.status == Business.PENDING
