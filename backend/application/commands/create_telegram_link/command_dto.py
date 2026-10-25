from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateTelegramLinkCommandDTO:
    account_id: UUID
