from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SearchBusinessesQueryDTO:
    account_id: UUID
    search: str = ""
