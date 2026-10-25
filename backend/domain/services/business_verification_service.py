from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class VerifiedPlace:
    place_id: str
    address: str


class BusinessVerificationService(ABC):
    """Comprueba que un teléfono es de un negocio real y abierto (Google Places)."""

    @abstractmethod
    def find(self, name, phone, city=""):
        """Devuelve VerifiedPlace o None."""
