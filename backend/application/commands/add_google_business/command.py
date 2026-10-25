from django.conf import settings

from domain.entities import Business
from domain.exceptions import BusinessRejected, PlaceUnavailable, SessionExpired
from domain.rules.country_language import language_for_country
from domain.rules.phone_format import parse_callable_phone


class AddGoogleBusinessCommand:
    """La persona elige un sitio de Google Maps. Se guarda verificado, solo con su place_id.

    Antes se comprueba con Google que sigue abierto y que su teléfono es uno al que Laia puede llamar.
    """

    def __init__(self, repositories, place_search_service):
        self.repositories = repositories
        self.place_search_service = place_search_service

    def execute(self, dto):
        account = self.repositories.accounts.find(dto.account_id)
        if not account:
            raise SessionExpired()
        existing = self.repositories.businesses.find_by_google_place(dto.google_place_id)
        if existing:
            if existing.status == Business.REJECTED:
                raise BusinessRejected()
            return existing

        place = self.place_search_service.details(dto.google_place_id)
        if not place:
            raise PlaceUnavailable()
        phone = parse_callable_phone(place.phone, settings.LAIA["ALLOWED_COUNTRIES"])
        business = Business.from_google(
            place_id=dto.google_place_id,
            label=(dto.label or "").strip() or place.name,
            country=phone.country,
            language=language_for_country(phone.country),
            created_by=account,
        )
        self.repositories.businesses.save(business)
        return business
