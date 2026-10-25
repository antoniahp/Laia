from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class FindPlacesQueryDTO:
    account_id: UUID
    search: str
    country: str = ""  # vacío = cerca de tu dirección; "DE" = buscar en Alemania
