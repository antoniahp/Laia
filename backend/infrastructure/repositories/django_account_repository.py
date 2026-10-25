from domain.entities import Account
from domain.repositories.account_repository import AccountRepository
from infrastructure.repositories._ids import valid_uuid


class DjangoAccountRepository(AccountRepository):
    def find(self, account_id):
        pk = valid_uuid(account_id)
        return Account.objects.filter(pk=pk).first() if pk else None

    def find_by_email(self, email):
        return Account.objects.filter(email=email).first()

    def find_by_link_code(self, link_code):
        if not link_code:
            return None
        return Account.objects.filter(telegram_link_code=link_code).first()

    def find_by_telegram_chat(self, chat_id):
        return Account.objects.filter(telegram_chat_id=chat_id).first()

    def list_admins_with_telegram(self):
        return list(Account.objects.filter(is_admin=True, telegram_chat_id__isnull=False))

    def save(self, account, fields=None):
        account.save(update_fields=fields) if fields and not account._state.adding else account.save()

    def delete(self, account):
        account.delete()  # los pedidos se borran en cascada; los negocios propuestos se quedan sin autor

    def unlink_telegram_chat(self, chat_id):
        Account.objects.filter(telegram_chat_id=chat_id).update(telegram_chat_id=None)
