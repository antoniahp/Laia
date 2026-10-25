import httpx
from django.conf import settings
from django.core.management.base import BaseCommand

from domain.entities import Account
from infrastructure.dependencies import get_repositories, get_token_service


class Command(BaseCommand):
    help = "Laia llama a tu negocio de prueba (por defecto «pizzeria bebé») a través del servidor en marcha."

    def add_arguments(self, parser):
        parser.add_argument("--negocio", default="pizzeria bebe")
        parser.add_argument("--pedido", default="1 pizza cuatro quesos")

    def handle(self, *args, **options):
        email = (settings.LAIA.get("ADMIN_EMAIL") or "").strip().lower()
        account = Account.objects.filter(email=email).first() or Account.objects.order_by("created_at").first()
        if not account:
            self.stdout.write(self.style.ERROR("No encuentro tu cuenta (ADMIN_EMAIL)."))
            return
        found = get_repositories().businesses.search_visible(account.id, options["negocio"], limit=1)
        if not found:
            self.stdout.write(self.style.ERROR(f"No encuentro «{options['negocio']}» en Mis sitios."))
            return
        business = found[0]
        token = get_token_service().issue(account.id)
        response = httpx.post(
            "http://localhost:8000/api/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={"business_id": str(business.id), "items": [options["pedido"]], "mode": "pedido"},
            timeout=30,
        )
        self.stdout.write(f"Llamando a {business.name}: {response.status_code} {response.text[:200]}")
