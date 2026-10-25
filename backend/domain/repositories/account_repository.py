from abc import ABC, abstractmethod


class AccountRepository(ABC):
    @abstractmethod
    def find(self, account_id):
        """Devuelve la cuenta o None."""

    @abstractmethod
    def find_by_email(self, email):
        pass

    @abstractmethod
    def find_by_link_code(self, link_code):
        pass

    @abstractmethod
    def find_by_telegram_chat(self, chat_id):
        pass

    @abstractmethod
    def list_admins_with_telegram(self):
        pass

    @abstractmethod
    def save(self, account, fields=None):
        """Guarda la cuenta (nueva o existente). Con fields, solo esos campos."""

    @abstractmethod
    def delete(self, account):
        """Borra la cuenta y todo lo suyo (pedidos y conversaciones)."""

    @abstractmethod
    def unlink_telegram_chat(self, chat_id):
        """Un chat de Telegram solo puede estar unido a una cuenta."""
