from ninja import Schema


class ReviewBusinessSchema(Schema):
    status: str | None = None  # verificado | rechazado | pendiente
    ivr_digits: str | None = None
    language: str | None = None
