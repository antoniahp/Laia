from abc import ABC, abstractmethod


class BusinessRepository(ABC):
    @abstractmethod
    def find(self, business_id):
        """Devuelve el negocio o None."""

    @abstractmethod
    def find_by_phone(self, phone):
        pass

    @abstractmethod
    def find_by_google_place(self, place_id):
        pass

    @abstractmethod
    def save(self, business, fields=None):
        pass

    @abstractmethod
    def search_visible(self, account_id, text="", limit=50):
        """Negocios verificados más los que ha propuesto esta cuenta."""

    @abstractmethod
    def list_by_status(self, status):
        pass
