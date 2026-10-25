from uuid import UUID

from ninja import Schema

from infrastructure.api.shared.schemas import BusinessSchema


class InterpretOrderSchema(Schema):
    command: str
    business_id: UUID | None = None


class OrderDraftSchema(Schema):
    mode: str
    items: list[str]
    alternatives: list[str]
    max_price: float | None
    ask_before_alternative: bool
    notes: str
    business_name: str
    business: BusinessSchema | None
