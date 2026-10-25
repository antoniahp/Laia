"""Comprueba la voz de Laia en ElevenLabs: python manage.py probar_voz"""

import asyncio
import base64
import json

import httpx
import websockets
from django.conf import settings
from django.core.management.base import BaseCommand

API = "https://api.elevenlabs.io/v1"


class Command(BaseCommand):
    help = "Lista las voces que puede usar tu clave de ElevenLabs y prueba la configurada."

    def handle(self, *args, **options):
        cfg = settings.LAIA
        key, voice_id, model = cfg["ELEVENLABS_API_KEY"], cfg["ELEVENLABS_VOICE_ID"], cfg["ELEVENLABS_MODEL"]
        headers = {"xi-api-key": key}
        self.stdout.write(f"Voz configurada: {voice_id or '(vacía)'}   Modelo: {model}")

        try:
            response = httpx.get(f"{API}/voices", headers=headers, timeout=20)
            if response.status_code == 200:
                voices = response.json().get("voices", [])
                self.stdout.write(f"\nVoces que puede usar tu clave ({len(voices)}):")
                for v in voices:
                    mark = "  <-- la tuya" if v.get("voice_id") == voice_id else ""
                    self.stdout.write(f"  {v.get('voice_id')}  {v.get('name')} ({v.get('category')}){mark}")
                if voice_id not in {v.get("voice_id") for v in voices}:
                    self.stdout.write(self.style.WARNING("\nTu voz NO está en la lista: añádela a «Mis voces» o copia uno de estos ID."))
            else:
                self.stdout.write(f"No pude listar voces ({response.status_code}): {response.text[:200]}")
        except Exception as error:  # noqa: BLE001
            self.stdout.write(f"No pude listar voces: {error!r}")

        try:
            response = httpx.post(
                f"{API}/text-to-speech/{voice_id}",
                headers=headers,
                timeout=30,
                json={"text": "Hola, soy la IA y llamo para hacer un pedido.", "model_id": model},
            )
        except Exception as error:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f"\nFALLA la prueba de voz: {error!r}"))
            return
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS(f"\nLA VOZ FUNCIONA ({len(response.content)} bytes de audio)."))
        else:
            self.stdout.write(self.style.ERROR(f"\nFALLA la prueba de voz ({response.status_code}): {response.text[:300]}"))

        if response.status_code == 200:
            self.stdout.write("\nPrueba del oído (ElevenLabs entiende lo que oye):")
            try:
                heard = httpx.post(
                    f"{API}/speech-to-text",
                    headers=headers,
                    timeout=60,
                    data={"model_id": "scribe_v1", "language_code": "es"},
                    files={"file": ("voz.mp3", response.content, "audio/mpeg")},
                )
                if heard.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f"EL OÍDO FUNCIONA: «{heard.json().get('text', '')}»"))
                    self.stdout.write("  → Pon STT_PROVIDER=elevenlabs en el .env para que Laia entienda mejor.")
                else:
                    self.stdout.write(self.style.ERROR(f"FALLA el oído ({heard.status_code}): {heard.text[:300]}"))
                    self.stdout.write("  → Activa el permiso «Speech to Text» en tu API key de ElevenLabs.")
            except Exception as error:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(f"FALLA el oído: {error!r}"))

        self.stdout.write("\nPrueba en directo (como en una llamada):")
        try:
            audio = asyncio.run(_live_test(voice_id, model, key, self.stdout.write))
        except Exception as error:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f"FALLA en directo: {error!r}"))
            return
        if audio:
            self.stdout.write(self.style.SUCCESS(f"EN DIRECTO FUNCIONA ({audio} bytes de audio)."))
        else:
            self.stdout.write(self.style.ERROR("EN DIRECTO NO LLEGA AUDIO: mira el mensaje de ElevenLabs de arriba."))


async def _live_test(voice_id, model, key, out):
    """Igual que en una llamada: conexión en directo, audio PCM a 16 kHz."""
    url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/multi-stream-input?model_id={model}&output_format=pcm_16000&auto_mode=true"
    audio = 0
    async with websockets.connect(url, additional_headers={"xi-api-key": key}) as ws:
        await ws.send(json.dumps({"text": " ", "context_id": "prueba"}))
        await ws.send(json.dumps({"text": "Hola, soy la IA y llamo para hacer un pedido. ", "context_id": "prueba", "flush": True}))
        await ws.send(json.dumps({"context_id": "prueba", "close_context": True}))
        try:
            while True:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if msg.get("audio"):
                    audio += len(base64.b64decode(msg["audio"]))
                other = {k: v for k, v in msg.items() if k not in ("audio", "alignment", "normalizedAlignment")}
                if other and not (set(other) <= {"contextId", "isFinal"}):
                    out(f"  ElevenLabs dice: {other}")
                if msg.get("isFinal"):
                    break
        except (TimeoutError, websockets.ConnectionClosed) as error:
            out(f"  Conexión terminada: {error!r}")
    return audio
