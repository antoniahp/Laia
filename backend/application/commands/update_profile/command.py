from django.conf import settings

from domain.exceptions import SessionExpired
from domain.rules.phone_format import parse_callable_phone


class UpdateProfileCommand:
    """Nombre, dirección de entrega y teléfono para el repartidor."""

    def __init__(self, repositories):
        self.repositories = repositories

    def execute(self, dto):
        account = self.repositories.accounts.find(dto.account_id)
        if not account:
            raise SessionExpired()
        fields = []
        if dto.name is not None:
            account.name = dto.name.strip()
            fields.append("name")
        if dto.address is not None:
            account.address = dto.address.strip()
            fields.append("address")
        if dto.phone is not None:
            phone = dto.phone.strip()
            account.phone = parse_callable_phone(phone, settings.LAIA["ALLOWED_COUNTRIES"]).e164 if phone else ""
            fields.append("phone")
        if fields:
            self.repositories.accounts.save(account, fields)
        return account
