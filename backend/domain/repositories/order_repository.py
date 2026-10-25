from abc import ABC, abstractmethod


class OrderRepository(ABC):
    @abstractmethod
    def find(self, order_id):
        """Devuelve el pedido o None."""

    @abstractmethod
    def find_for_account(self, account_id, order_id):
        """El pedido solo si es de esa cuenta."""

    @abstractmethod
    def save(self, order, fields=None):
        pass

    @abstractmethod
    def count_since(self, account_id, since):
        """Llamadas que ha pedido esta cuenta desde esa fecha."""

    @abstractmethod
    def list_for_account(self, account_id, limit=50):
        pass

    @abstractmethod
    def forget_conversations_before(self, cutoff):
        """Vacía la conversación de los pedidos anteriores a esa fecha. Devuelve cuántos."""
