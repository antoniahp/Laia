"""Páginas legales públicas: /legal/privacidad/, /legal/terminos/, /legal/negocios/."""

from django.conf import settings
from django.http import Http404
from django.shortcuts import render

PAGES = {"privacidad", "terminos", "negocios"}


def legal_page(request, page):
    if page not in PAGES:
        raise Http404()
    cfg = settings.LAIA
    return render(
        request,
        f"legal/{page}.html",
        {
            "owner": cfg["LEGAL_OWNER_NAME"],
            "email": cfg["LEGAL_CONTACT_EMAIL"],
            "version": cfg["TERMS_VERSION"],
            "retention_days": cfg["RETENTION_DAYS"],
            "stt_elevenlabs": cfg["STT_PROVIDER"] == "elevenlabs",
        },
    )
