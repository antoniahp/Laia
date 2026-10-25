"""Lo que ve la app de cada entidad."""

from datetime import datetime
from uuid import UUID

from ninja import Schema

from domain.rules.languages import language_name


class AccountSchema(Schema):
    id: UUID
    email: str
    name: str
    address: str
    phone: str
    is_admin: bool
    telegram_linked: bool
    terms_version: str

    @staticmethod
    def resolve_telegram_linked(obj):
        return obj.has_telegram


class BusinessSchema(Schema):
    id: UUID
    name: str
    phone: str
    country: str
    language: str
    address: str
    status: str
    source: str

    @staticmethod
    def resolve_phone(obj):
        return obj.phone or ""  # los de Google no guardan teléfono


class PlaceCandidateSchema(Schema):
    """Un sitio encontrado. Si from_google es true, la app debe mostrar «Google Maps» junto a él."""

    name: str
    address: str
    country: str
    language: str
    google_place_id: str | None
    business_id: str | None
    from_google: bool


class BusinessAdminSchema(BusinessSchema):
    ivr_digits: str
    created_by: UUID | None

    @staticmethod
    def resolve_created_by(obj):
        return obj.created_by_id


class OrderSchema(Schema):
    id: UUID
    status: str
    business_name: str
    language: str
    language_name: str
    mode: str
    items: list[str]
    alternatives: list[str]
    max_price: float | None
    events: list[str]
    transcript: list[dict]
    pending_question: str | None
    result: dict | None
    created_at: datetime | None

    @staticmethod
    def resolve_language_name(obj):
        return language_name(obj.language)


class TokenSchema(Schema):
    token: str
    user: AccountSchema


class DetailSchema(Schema):
    detail: str
