from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TransferCallCommandDTO:
    account_id: UUID
    order_id: UUID
