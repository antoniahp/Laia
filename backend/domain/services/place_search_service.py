from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class FoundPlace:
    """Datos de Google Maps. Solo se muestran en el momento: no se guardan (salvo place_id)."""

    place_id: str
    name: str
    phone: str
    address: str


class PlaceSearchService(ABC):
    """Busca negocios reales (Google Maps)."""

    @abstractmethod
    def is_enabled(self):
        """True si el servicio está configurado."""

    @abstractmethod
    def search(self, text, near="", country=""):
        """Negocios abiertos con teléfono. near: dirección para buscar cerca. country: código ISO para buscar en otro país."""

    @abstractmethod
    def details(self, place_id):
        """Datos actuales de un negocio (FoundPlace) o None si ya no existe o no tiene teléfono."""
