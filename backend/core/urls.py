from django.contrib import admin
from django.urls import path

from infrastructure.api.api import api
from infrastructure.legal.views import legal_page
from infrastructure.webhooks.api import webhooks_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("legal/<slug:page>/", legal_page, name="legal"),
    path("", webhooks_api.urls),
]
