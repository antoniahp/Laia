import json
import logging
import re

import httpx
from django.conf import settings

from domain.exceptions import LanguageModelUnavailable
from domain.services.language_model_service import LanguageModelService, ParsedCommand

logger = logging.getLogger(__name__)


def extract_json(message):
    """Gemma puede envolver el JSON en ```json ... ``` o dejarlo en «thinking»: lo saca de donde esté."""
    for text in (message.get("content") or "", message.get("thinking") or ""):
        text = text.strip()
        if not text:
            continue
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
        candidates = [fenced.group(1)] if fenced else []
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            candidates.append(text[start : end + 1])
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Respuesta sin JSON: {(message.get('content') or '')[:200]!r}")


SCHEMA = {
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": ["pedido", "reserva", "consulta"]},
        "items": {"type": "array", "items": {"type": "string"}},
        "alternatives": {"type": "array", "items": {"type": "string"}},
        "max_price": {"type": ["number", "null"]},
        "ask_before_alternative": {"type": "boolean"},
        "notes": {"type": "string"},
        "business_name": {"type": "string"},
    },
    "required": ["mode", "items", "alternatives", "max_price", "ask_before_alternative", "notes", "business_name"],
}

PROMPT = """Eres el intérprete de órdenes de Laia, una asistente que llama a negocios.
Convierte la orden del usuario en JSON. Reglas:
- items: lo que quiere pedir, con cantidad si la dice ("2 pizzas cuatro quesos").
- alternatives: qué pedir si no hay lo principal, en orden. Vacío si no lo dice.
- max_price: precio máximo total en euros si lo dice ("si es menos de 20 euros" -> 20). Si no, null.
- ask_before_alternative: true si dice que le pregunte antes de cambiar, o si dice
  "otra cosa" sin concretar cuál.
- mode: "reserva" si quiere reservar mesa, cita u habitación ("reserva para 4 el sábado a las 21h");
  "consulta" si solo quiere saber precio, horario, stock o envío sin comprar; si no, "pedido".
- items: en una reserva, lo que hay que reservar con personas, día y hora ("mesa para 4, sábado 21:00").
- notes: peticiones extra (sin cebolla, bien hecha, preguntar envío a España...).
- business_name: el negocio al que hay que llamar, tal como lo dice ("pide en Tres Hermanas" -> "Tres Hermanas",
  "llama a la pizzería Luigi de Gràcia" -> "pizzería Luigi Gràcia"). Vacío si no nombra ninguno.
  Quita "de mi agenda", "de mis sitios", "de mi lista" y similares: "pide en la pizzería Paco de mi agenda" -> "pizzería Paco".
La orden puede venir en español, inglés u otro idioma: entiéndela igual. Escribe items, alternatives y notes en el
idioma en que te hablan, y deja business_name tal cual (es un nombre propio). Los valores de mode son siempre
"pedido", "reserva" o "consulta".
Ejemplos:
- "Order a pepperoni pizza maximum 20 euros from pizzeria Picciolo" ->
  {"mode": "pedido", "items": ["1 pepperoni pizza"], "alternatives": [], "max_price": 20,
   "ask_before_alternative": false, "notes": "", "business_name": "pizzeria Picciolo"}
- "Book a table for 2 on Friday at 8pm at La Tagliatella" ->
  {"mode": "reserva", "items": ["table for 2, Friday 20:00"], "alternatives": [], "max_price": null,
   "ask_before_alternative": false, "notes": "", "business_name": "La Tagliatella"}
- "Pide una cuatro quesos en Tres Hermanas, si no hay una margarita" ->
  {"mode": "pedido", "items": ["1 pizza cuatro quesos"], "alternatives": ["1 pizza margarita"], "max_price": null,
   "ask_before_alternative": false, "notes": "", "business_name": "Tres Hermanas"}
Responde solo con el JSON."""


class OllamaLanguageModelService(LanguageModelService):
    """Gemma (open-weight) vía Ollama, en local o en Ollama Cloud."""

    def __init__(self):
        cfg = settings.LAIA
        self.host = cfg["OLLAMA_HOST"]
        self.model = cfg["OLLAMA_MODEL"]
        self.api_key = cfg["OLLAMA_API_KEY"]

    def translate(self, text, source_language, target_language="es"):
        names = {"es": "español", "en": "inglés", "de": "alemán", "fr": "francés", "it": "italiano", "pt": "portugués", "ja": "japonés"}
        prompt = (
            f"Traduce del {names.get(source_language, source_language)} al {names.get(target_language, target_language)} "
            "esta frase de una llamada telefónica. Responde solo con la traducción, sin comillas ni explicaciones."
        )
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = httpx.post(
                f"{self.host}/api/chat",
                headers=headers,
                timeout=30,
                json={
                    "model": self.model,
                    "stream": False,
                    "think": False,
                    "options": {"temperature": 0},
                    "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}],
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip().strip('"')
        except Exception as error:  # noqa: BLE001
            raise LanguageModelUnavailable() from error

    def parse_command(self, text):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = httpx.post(
                f"{self.host}/api/chat",
                headers=headers,
                timeout=60,
                json={
                    "model": self.model,
                    "stream": False,
                    "think": False,
                    "format": SCHEMA,
                    "options": {"temperature": 0},
                    "messages": [{"role": "system", "content": PROMPT}, {"role": "user", "content": text}],
                },
            )
            response.raise_for_status()
            data = extract_json(response.json()["message"])
        except httpx.HTTPStatusError as error:
            body = error.response.text[:300]
            logger.error("Ollama respondió %s con el modelo %s: %s", error.response.status_code, self.model, body)
            raise LanguageModelUnavailable() from error
        except Exception as error:  # noqa: BLE001
            logger.error("No pude usar Ollama (%s, modelo %s): %r", self.host, self.model, error)
            raise LanguageModelUnavailable() from error
        logger.info("Orden: %r -> %s", text, json.dumps(data, ensure_ascii=False))
        return ParsedCommand(
            mode=data.get("mode", "pedido"),
            items=[str(i) for i in data.get("items", []) if str(i).strip()],
            alternatives=[str(a) for a in data.get("alternatives", []) if str(a).strip()],
            max_price=data.get("max_price"),
            ask_before_alternative=bool(data.get("ask_before_alternative", False)),
            notes=data.get("notes") or "",
            business_name=(data.get("business_name") or "").strip(),
        )
