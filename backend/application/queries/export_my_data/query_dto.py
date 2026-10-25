from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ExportMyDataQueryDTO:
    account_id: UUID
