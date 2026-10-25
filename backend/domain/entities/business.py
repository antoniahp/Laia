from django.db import models

from domain.entities.base_model import BaseModel
from domain.exceptions import BusinessNotVerified, InvalidBusinessData, InvalidIvrDigits
from domain.rules.languages import LANGUAGES


class Business(BaseModel):
    """Un negocio del directorio. Laia solo llama a los verificados.

    Dos orígenes:
    - manual: alguien lo propone con su teléfono y lo aprueba una administradora.
    - google: encontrado en Google Maps. Por las condiciones de Google solo guardamos su place_id;
      el nombre que se ve es el que usó la persona, y el teléfono se pide a Google al llamar.
    """

    PENDING = "pendiente"
    VERIFIED = "verificado"
    REJECTED = "rechazado"
    STATUSES = [(PENDING, "Pendiente"), (VERIFIED, "Verificado"), (REJECTED, "Rechazado")]

    MANUAL = "manual"
    GOOGLE = "google"
    SOURCES = [(MANUAL, "Propuesto a mano"), (GOOGLE, "Google Maps")]

    name = models.CharField("nombre", max_length=160)
    source = models.CharField("origen", max_length=10, choices=SOURCES, default=MANUAL)
    phone = models.CharField("teléfono", max_length=32, unique=True, null=True, blank=True)  # solo los manuales
    google_place_id = models.CharField(max_length=300, unique=True, null=True, blank=True)
    country = models.CharField("país", max_length=2)
    language = models.CharField("idioma", max_length=5, default="es")
    address = models.CharField("dirección", max_length=300, blank=True)  # solo los manuales
    status = models.CharField("estado", max_length=20, choices=STATUSES, default=PENDING, db_index=True)
    verified_by = models.CharField(max_length=40, blank=True)  # google_places | admin
    ivr_digits = models.CharField(
        "teclas del menú", max_length=32, blank=True, help_text="Se marcan al conectar. w = pausa de medio segundo."
    )
    created_by = models.ForeignKey("domain.Account", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "negocio"

    def __str__(self):
        return f"{self.name} ({self.status})"

    # ---------- creación ----------

    @classmethod
    def from_google(cls, place_id, label, country, language, created_by=None):
        """Negocio confirmado por Google Maps: verificado desde el primer momento."""
        cls.check_data(label, language)
        return cls(
            name=label.strip()[:160],
            source=cls.GOOGLE,
            google_place_id=place_id,
            country=country,
            language=language,
            status=cls.VERIFIED,
            verified_by="google_places",
            created_by=created_by,
        )

    # ---------- reglas ----------

    @staticmethod
    def check_data(name, language):
        if len((name or "").strip()) < 2 or language not in LANGUAGES:
            raise InvalidBusinessData()

    @property
    def is_verified(self):
        return self.status == self.VERIFIED

    @property
    def is_from_google(self):
        return self.source == self.GOOGLE

    def verify(self, by):
        self.status = self.VERIFIED
        self.verified_by = by

    def reject(self):
        self.status = self.REJECTED
        self.verified_by = "admin"

    def set_ivr_digits(self, digits):
        if len(digits) > 32 or any(c not in "0123456789*#w" for c in digits):
            raise InvalidIvrDigits()
        self.ivr_digits = digits

    def ensure_callable(self):
        if not self.is_verified:
            raise BusinessNotVerified()
