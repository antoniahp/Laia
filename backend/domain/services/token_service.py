from abc import ABC, abstractmethod


class TokenService(ABC):
    """Sesiones de la app."""

    @abstractmethod
    def issue(self, account_id):
        pass

    @abstractmethod
    def read(self, token):
        """Devuelve el id de la cuenta o None si el token no vale o ha caducado."""
