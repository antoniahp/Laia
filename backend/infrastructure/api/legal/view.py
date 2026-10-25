from django.conf import settings
from ninja import Router, Schema

router = Router(tags=["legal"])


class LegalInfoSchema(Schema):
    terms_version: str
    privacy_url: str
    terms_url: str
    business_info_url: str
    retention_days: int


@router.get("/legal", response=LegalInfoSchema, auth=None)
def legal_info(request):
    base = request.build_absolute_uri("/").rstrip("/")
    cfg = settings.LAIA
    return {
        "terms_version": cfg["TERMS_VERSION"],
        "privacy_url": f"{base}/legal/privacidad/",
        "terms_url": f"{base}/legal/terminos/",
        "business_info_url": f"{base}/legal/negocios/",
        "retention_days": cfg["RETENTION_DAYS"],
    }
