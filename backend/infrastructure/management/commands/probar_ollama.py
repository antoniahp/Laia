"""Prueba Gemma en Ollama con una orden de ejemplo: python manage.py probar_ollama"""

import time

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand

from infrastructure.services.ollama_language_model_service import OllamaLanguageModelService


class Command(BaseCommand):
    help = "Comprueba que Ollama responde y que el modelo entiende una orden."

    def handle(self, *args, **options):
        cfg = settings.LAIA
        host, model = cfg["OLLAMA_HOST"], cfg["OLLAMA_MODEL"]
        self.stdout.write(f"Servidor: {host}\nModelo:   {model}\nClave:    {'puesta' if cfg['OLLAMA_API_KEY'] else 'NO PUESTA'}")

        headers = {"Authorization": f"Bearer {cfg['OLLAMA_API_KEY']}"} if cfg["OLLAMA_API_KEY"] else {}
        try:
            tags = httpx.get(f"{host}/api/tags", headers=headers, timeout=20)
            names = [m.get("name") for m in tags.json().get("models", [])] if tags.status_code == 200 else []
            if names:
                ok = model in names
                self.stdout.write(f"Modelos disponibles ({len(names)}): {'el tuyo SÍ está' if ok else 'el tuyo NO está'}")
                if not ok:
                    gemmas = [n for n in names if "gemma" in (n or "")]
                    self.stdout.write("Modelos Gemma que sí hay: " + (", ".join(gemmas) or "ninguno"))
        except Exception as error:  # noqa: BLE001
            self.stdout.write(f"No pude listar modelos: {error!r}")

        start = time.time()
        try:
            parsed = OllamaLanguageModelService().parse_command(
                "Pide una pizza cuatro quesos en Tres Hermanas, si no hay una margarita, máximo 20 euros"
            )
        except Exception as error:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f"FALLA: {error!r}. Mira la línea de error de arriba."))
            return
        self.stdout.write(self.style.SUCCESS(f"FUNCIONA en {time.time() - start:.1f} s: {parsed}"))
