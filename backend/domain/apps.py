from django.apps import AppConfig


class DomainConfig(AppConfig):
    """La capa de dominio es la app de Django que contiene los modelos y sus migraciones."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "domain"
    verbose_name = "Laia"
