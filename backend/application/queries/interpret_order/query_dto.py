from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class InterpretOrderQueryDTO:
    account_id: UUID
    command: str
    business_id: UUID | None = None  # si no viene, la persona ha dicho el sitio en la frase
