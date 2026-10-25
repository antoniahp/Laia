from ninja import Schema


class UpdateProfileSchema(Schema):
    name: str | None = None
    address: str | None = None
    phone: str | None = None


class TelegramLinkSchema(Schema):
    url: str
