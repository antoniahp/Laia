import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from domain.entities import Account


class Command(BaseCommand):
    help = "Crea el usuario del panel /admin con DJANGO_ADMIN_USER y DJANGO_ADMIN_PASSWORD si no existe."

    def handle(self, *args, **options):
        self._promote_admin_account()
        username = os.getenv("DJANGO_ADMIN_USER", "").strip()
        password = os.getenv("DJANGO_ADMIN_PASSWORD", "").strip()
        if not username or not password:
            self.stdout.write("Sin DJANGO_ADMIN_USER/DJANGO_ADMIN_PASSWORD: no creo usuario del panel.")
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"El usuario del panel {username} ya existe.")
            return
        User.objects.create_superuser(username=username, email="", password=password)
        self.stdout.write(self.style.SUCCESS(f"Usuario del panel {username} creado."))

    def _promote_admin_account(self):
        """La cuenta de la app con el email de ADMIN_EMAIL es administradora, aunque se creara antes."""
        email = (settings.LAIA.get("ADMIN_EMAIL") or "").strip().lower()
        if not email:
            return
        updated = Account.objects.filter(email=email, is_admin=False).update(is_admin=True)
        if updated:
            self.stdout.write(self.style.SUCCESS(f"{email} ahora es administradora en la app."))
