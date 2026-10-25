from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DeleteAccountCommandDTO:
    account_id: UUID
