import logging

import httpx
from django.conf import settings

from domain.rules.country_language import country_name
from domain.rules.phone_format import same_phone
from domain.services.business_verification_service import BusinessVerificationService, VerifiedPlace
from domain.services.place_search_service import FoundPlace, PlaceSearchService

logger = logging.getLogger(__name__)

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"
SEARCH_FIELDS = "places.id,places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.businessStatus"
DETAILS_FIELDS = "id,displayName,formattedAddress,internationalPhoneNumber,businessStatus"
LOCATION_FIELDS = "places.location"
NEARBY_METERS = 15000


def _found(place):
    if not place.get("internationalPhoneNumber") or place.get("businessStatus") not in (None, "OPERATIONAL"):
        return None
    return FoundPlace(
        place_id=place.get("id", ""),
        name=place.get("displayName", {}).get("text", ""),
        phone=place["internationalPhoneNumber"],
        address=place.get("formattedAddress", ""),
    )


class GooglePlacesService(BusinessVerificationService, PlaceSearchService):
    """Google Places API (New).

    Condiciones de Google: solo el place_id se puede guardar. Nombre, dirección y teléfono se piden
    cada vez que hacen falta y se muestran con la atribución «Google Maps».
    """

    def __init__(self):
        self.api_key = settings.LAIA["GOOGLE_PLACES_API_KEY"]

    def is_enabled(self):
        return bool(self.api_key)

    def _headers(self, fields):
        return {"X-Goog-Api-Key": self.api_key, "X-Goog-FieldMask": fields}

    def _search_text(self, body, fields):
        response = httpx.post(SEARCH_URL, headers=self._headers(fields), json={"languageCode": "es", **body}, timeout=15)
        response.raise_for_status()
        return response.json().get("places", [])

    def _location_of(self, address):
        if not address:
            return None
        try:
            places = self._search_text({"textQuery": address, "maxResultCount": 1}, LOCATION_FIELDS)
            return places[0]["location"] if places else None
        except Exception as error:  # noqa: BLE001
            logger.warning("No pude localizar la dirección: %s", error)
            return None

    def search(self, text, near="", country=""):
        if not self.api_key:
            return []
        body = {"textQuery": text, "maxResultCount": 10}
        if country:
            body["textQuery"] = f"{text}, {country_name(country)}"
            body["regionCode"] = country
        else:
            location = self._location_of(near)
            if location:
                body["locationBias"] = {"circle": {"center": location, "radius": NEARBY_METERS}}
        try:
            places = self._search_text(body, SEARCH_FIELDS)
        except Exception as error:  # noqa: BLE001
            logger.warning("Google Places falló: %s", error)
            return []
        return [found for found in map(_found, places) if found]

    def details(self, place_id):
        if not self.api_key or not place_id:
            return None
        try:
            response = httpx.get(
                DETAILS_URL.format(place_id=place_id.removeprefix("places/")),
                headers=self._headers(DETAILS_FIELDS),
                params={"languageCode": "es"},
                timeout=15,
            )
            response.raise_for_status()
            return _found(response.json())
        except Exception as error:  # noqa: BLE001
            logger.warning("Google Place Details falló: %s", error)
            return None

    def find(self, name, phone, city=""):
        if not self.api_key:
            return None
        try:
            places = self._search_text({"textQuery": f"{name} {city}".strip(), "maxResultCount": 5}, SEARCH_FIELDS)
        except Exception as error:  # noqa: BLE001
            logger.warning("Google Places falló: %s", error)
            return None
        for place in places:
            found = _found(place)
            if found and same_phone(found.phone, phone):
                return VerifiedPlace(place_id=found.place_id, address="")
        return None
