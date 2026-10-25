from django.conf import settings
from django.core.management.base import BaseCommand

REQUIRED = [
    "ADMIN_EMAIL",
    "PUBLIC_URL",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_FROM_NUMBER",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "OLLAMA_API_KEY",
]
OPTIONAL = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_USERNAME", "GOOGLE_PLACES_API_KEY", "SIGNUP_CODE"]


class Command(BaseCommand):
    help = "Comprueba qué variables de entorno faltan."

    def handle(self, *args, **options):
        cfg = settings.LAIA
        missing = [k for k in REQUIRED if not cfg.get(k)]
        if missing:
            self.stdout.write(self.style.WARNING(f"Faltan para poder llamar: {', '.join(missing)}"))
        else:
            self.stdout.write(self.style.SUCCESS("Todo lo necesario para llamar está configurado."))
        optional = [k for k in OPTIONAL if not cfg.get(k)]
        if optional:
            self.stdout.write(f"Opcionales sin configurar: {', '.join(optional)}")
