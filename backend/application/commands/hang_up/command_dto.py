from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class HangUpCommandDTO:
    account_id: UUID
    order_id: UUID
