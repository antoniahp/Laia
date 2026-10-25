from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ProposeBusinessCommandDTO:
    account_id: UUID
    name: str
    phone: str
    language: str = "es"
    city: str = ""
