from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ReviewBusinessCommandDTO:
    admin_id: UUID
    business_id: UUID
    status: str | None = None  # verificado | rechazado | pendiente
    ivr_digits: str | None = None
    language: str | None = None
