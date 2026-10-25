from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListBusinessesByStatusQueryDTO:
    admin_id: UUID
    status: str = "pendiente"
