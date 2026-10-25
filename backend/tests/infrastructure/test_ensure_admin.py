from django.core.management import call_command

from domain.entities import Account


def test_admin_email_account_becomes_admin(db, settings, capsys):
    settings.LAIA = {**settings.LAIA, "ADMIN_EMAIL": "Toni@Laia.dev"}
    account = Account(email="toni@laia.dev")
    account.set_password("12345678")
    account.save()
    call_command("ensure_admin")
    account.refresh_from_db()
    assert account.is_admin
