import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from domain.entities.base_model import BaseModel
from domain.exceptions import InvalidEmail, NotAdmin, WeakPassword


def new_link_code():
    return secrets.token_urlsafe(12)


class Account(BaseModel):
    """Una persona que usa Laia para que llame por ella."""

    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    name = models.CharField("nombre", max_length=120, blank=True)
    address = models.CharField("dirección de entrega", max_length=300, blank=True)
    phone = models.CharField("teléfono", max_length=32, blank=True)
    is_admin = models.BooleanField("administradora", default=False)
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    telegram_link_code = models.CharField(max_length=32, unique=True, default=new_link_code)
    terms_version = models.CharField("versión de condiciones aceptada", max_length=20, blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["email"]
        verbose_name = "cuenta"

    def __str__(self):
        return self.email

    # ---------- reglas ----------

    @staticmethod
    def normalize_email(email):
        email = (email or "").strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise InvalidEmail()
        return email

    def set_password(self, password):
        if len(password or "") < 8:
            raise WeakPassword()
        self.password_hash = make_password(password)

    def check_password(self, password):
        return check_password(password, self.password_hash)

    @property
    def has_telegram(self):
        return self.telegram_chat_id is not None

    def renew_link_code(self):
        self.telegram_link_code = new_link_code()
        return self.telegram_link_code

    def link_telegram(self, chat_id):
        self.telegram_chat_id = chat_id
        self.renew_link_code()  # el enlace solo sirve una vez

    def accept_terms(self, version, when):
        self.terms_version = version
        self.terms_accepted_at = when

    def require_admin(self):
        if not self.is_admin:
            raise NotAdmin()
