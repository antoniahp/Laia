from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class PlaceOrderCommandDTO:
    account_id: UUID
    business_id: UUID
    items: list = field(default_factory=list)
    mode: str = "pedido"
    alternatives: list = field(default_factory=list)
    max_price: float | None = None
    notes: str = ""
    ask_before_alternative: bool = False
