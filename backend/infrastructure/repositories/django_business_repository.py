from django.db.models import Q

from domain.entities import Business
from domain.repositories.business_repository import BusinessRepository
from domain.rules.name_match import name_matches
from infrastructure.repositories._ids import valid_uuid


class DjangoBusinessRepository(BusinessRepository):
    def find(self, business_id):
        pk = valid_uuid(business_id)
        return Business.objects.select_related("created_by").filter(pk=pk).first() if pk else None

    def find_by_phone(self, phone):
        return Business.objects.filter(phone=phone).first()

    def find_by_google_place(self, place_id):
        if not place_id:
            return None
        return Business.objects.filter(google_place_id=place_id).first()

    def save(self, business, fields=None):
        business.save(update_fields=fields) if fields and not business._state.adding else business.save()

    def search_visible(self, account_id, text="", limit=50):
        businesses = Business.objects.filter(Q(status=Business.VERIFIED) | Q(created_by_id=account_id)).order_by("name")
        if not text:
            return list(businesses[:limit])
        # sin tildes ni mayúsculas: «pizzería Bebé» encuentra «pizzeria bebé»
        return [b for b in businesses[:2000] if name_matches(text, b.name)][:limit]

    def list_by_status(self, status):
        return list(Business.objects.filter(status=status).order_by("created_at"))
