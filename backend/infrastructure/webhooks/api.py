"""Webhooks externos (Twilio y Telegram): sin sesión de usuario, cada uno con su propia verificación."""

from ninja import NinjaAPI

from infrastructure.webhooks.telegram.view import router as telegram
from infrastructure.webhooks.twilio.view import router as twilio

webhooks_api = NinjaAPI(title="Laia webhooks", urls_namespace="webhooks", docs_url=None, openapi_url=None)
webhooks_api.add_router("", twilio)
webhooks_api.add_router("", telegram)
