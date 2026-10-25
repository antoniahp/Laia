from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UpdateProfileCommandDTO:
    account_id: UUID
    name: str | None = None
    address: str | None = None
    phone: str | None = None
