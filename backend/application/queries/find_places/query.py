from dataclasses import dataclass

from django.conf import settings

from domain.exceptions import (
    CountryNotAllowed,
    InvalidPhone,
    PlaceNotFound,
    PlaceSearchNotConfigured,
    PremiumRateNumber,
    SessionExpired,
)
from domain.rules.country_language import language_for_country
from domain.rules.phone_format import parse_callable_phone

MAX_RESULTS = 6


@dataclass(frozen=True)
class PlaceCandidate:
    """Un sitio que puede ser el que buscas. Lo de Google se muestra pero no se guarda."""

    name: str
    address: str
    country: str
    language: str
    google_place_id: str | None = None
    business_id: str | None = None  # si ya está en tu lista
    from_google: bool = False


class FindPlacesQuery:
    """Busca el sitio que nombra la persona: primero en el directorio, luego en Google Maps."""

    def __init__(self, repositories, place_search_service):
        self.repositories = repositories
        self.place_search_service = place_search_service

    def execute(self, dto):
        account = self.repositories.accounts.find(dto.account_id)
        if not account:
            raise SessionExpired()
        text = (dto.search or "").strip()
        if len(text) < 2:
            raise PlaceNotFound("Dime el nombre del sitio.")
        country = (dto.country or "").upper()

        candidates = [
            PlaceCandidate(
                name=b.name,
                address=b.address,
                country=b.country,
                language=b.language,
                google_place_id=b.google_place_id,
                business_id=str(b.id),
            )
            for b in self.repositories.businesses.search_visible(account.id, text)
            if b.is_verified and (not country or b.country == country)
        ]

        # Si está en tus sitios, es ese: no hace falta mirar en Google
        if candidates:
            return candidates[:MAX_RESULTS]
        if not self.place_search_service.is_enabled():
            if not candidates:
                raise PlaceSearchNotConfigured()
            return candidates[:MAX_RESULTS]

        known = {c.google_place_id for c in candidates if c.google_place_id}
        near = "" if country else account.address
        for place in self.place_search_service.search(text, near=near, country=country):
            if place.place_id in known:
                continue
            try:
                phone = parse_callable_phone(place.phone, settings.LAIA["ALLOWED_COUNTRIES"])
            except (InvalidPhone, CountryNotAllowed, PremiumRateNumber):
                continue  # Laia nunca llama a esos números, aunque estén en Google
            if country and phone.country != country:
                continue
            saved = self.repositories.businesses.find_by_google_place(place.place_id)
            if saved and saved.status == saved.REJECTED:
                continue
            candidates.append(
                PlaceCandidate(
                    name=place.name,
                    address=place.address,
                    country=phone.country,
                    language=language_for_country(phone.country),
                    google_place_id=place.place_id,
                    business_id=str(saved.id) if saved else None,
                    from_google=True,
                )
            )
            if len(candidates) >= MAX_RESULTS:
                break
        if not candidates:
            raise PlaceNotFound()
        return candidates
