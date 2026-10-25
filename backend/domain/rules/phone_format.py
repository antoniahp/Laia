"""Teléfonos: Laia nunca llama a números de pago ni a países no permitidos."""

from dataclasses import dataclass

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberType

from domain.exceptions import CountryNotAllowed, InvalidPhone, PremiumRateNumber

# Fijos, móviles y gratuitos. Fuera: tarificación especial (806, 905), coste compartido (902), personales...
ALLOWED_TYPES = {
    PhoneNumberType.FIXED_LINE,
    PhoneNumberType.MOBILE,
    PhoneNumberType.FIXED_LINE_OR_MOBILE,
    PhoneNumberType.TOLL_FREE,
}


@dataclass(frozen=True)
class CallablePhone:
    e164: str
    country: str


def parse_callable_phone(raw, allowed_countries, default_region="ES"):
    """Devuelve el teléfono en formato +34... y su país, o lanza un error claro."""
    try:
        number = phonenumbers.parse(raw or "", default_region)
    except NumberParseException:
        raise InvalidPhone()
    if not phonenumbers.is_valid_number(number):
        raise InvalidPhone("Ese teléfono no es válido.")

    country = phonenumbers.region_code_for_number(number) or ""
    if country not in allowed_countries:
        raise CountryNotAllowed(f"Laia todavía no llama a ese país ({country or 'desconocido'}).")
    if phonenumbers.number_type(number) not in ALLOWED_TYPES:
        raise PremiumRateNumber()
    return CallablePhone(phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164), country)


def same_phone(a, b, default_region="ES"):
    try:
        fmt = phonenumbers.PhoneNumberFormat.E164
        return phonenumbers.format_number(phonenumbers.parse(a, default_region), fmt) == phonenumbers.format_number(
            phonenumbers.parse(b, default_region), fmt
        )
    except NumberParseException:
        return False
