from uuid import UUID

from ninja import Schema


class PlaceOrderSchema(Schema):
    business_id: UUID
    items: list[str]
    mode: str = "pedido"
    alternatives: list[str] = []
    max_price: float | None = None
    notes: str = ""
    ask_before_alternative: bool = False
