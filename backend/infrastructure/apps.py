from django.apps import AppConfig


class InfrastructureConfig(AppConfig):
    """Capa de infraestructura: API, webhooks, voz, admin, adaptadores (Twilio, Telegram, IA) y comandos de consola."""

    name = "infrastructure"
    verbose_name = "Infraestructura"
