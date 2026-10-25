"""Versiones falsas de los puertos para no llamar a Twilio, Telegram, Google ni a la IA en los tests."""

from domain.exceptions import LanguageModelUnavailable, MessageNotSent
from domain.services.business_verification_service import BusinessVerificationService, VerifiedPlace
from domain.services.call_service import CallService
from domain.services.language_model_service import LanguageModelService, ParsedCommand
from domain.services.message_service import MessageService
from domain.services.place_search_service import FoundPlace, PlaceSearchService


class FakeMessageService(MessageService):
    def __init__(self, enabled=True, fail=False):
        self.enabled = enabled
        self.fail = fail
        self.sent = []
        self.answered_buttons = []

    def is_enabled(self):
        return self.enabled

    def send(self, chat_id, text, buttons=None):
        if self.fail:
            raise MessageNotSent("Telegram caído")
        self.sent.append({"chat_id": chat_id, "text": text, "buttons": buttons or []})
        return str(100 + len(self.sent))

    def answer_button(self, callback_id, text=""):
        self.answered_buttons.append(text)

    def remove_buttons(self, chat_id, message_id):
        pass

    def link_url(self, link_code):
        return f"https://t.me/laia_bot?start={link_code}" if self.enabled else None


class FakeCallService(CallService):
    def __init__(self, fail=False, authentic=True):
        self.fail = fail
        self.authentic = authentic
        self.calls = []
        self.hung_up = []
        self.transfers = []

    def place_call(self, to, order_id, secret, ivr_digits=""):
        if self.fail:
            raise RuntimeError("Twilio caído")
        self.calls.append({"to": to, "order_id": order_id, "secret": secret, "ivr_digits": ivr_digits})
        return f"CA{len(self.calls)}"

    def hang_up(self, call_id):
        self.hung_up.append(call_id)

    def transfer(self, call_id, to, message, language):
        if self.fail:
            raise RuntimeError("Twilio caído")
        self.transfers.append({"call_id": call_id, "to": to, "message": message, "language": language})

    def is_request_authentic(self, url, params, signature):
        return self.authentic


class FakeVerificationService(BusinessVerificationService):
    def __init__(self, place=None):
        self.place = place

    def find(self, name, phone, city=""):
        return self.place


class FakeLanguageModelService(LanguageModelService):
    """Sin respuesta configurada se comporta como si Ollama estuviera apagado."""

    def __init__(self, parsed=None, translations=None):
        self.parsed = parsed
        self.translations = translations or {}
        self.received = []

    def parse_command(self, text):
        self.received.append(text)
        if self.parsed is None:
            raise LanguageModelUnavailable()
        return self.parsed

    def translate(self, text, source_language, target_language="es"):
        return self.translations.get(text, f"[{target_language}] {text}")


def pizza_command(**overrides):
    data = {
        "mode": "pedido",
        "items": ["pizza cuatro quesos"],
        "alternatives": ["margarita"],
        "max_price": 20,
        "ask_before_alternative": False,
        "notes": "",
    }
    data.update(overrides)
    return ParsedCommand(**data)


def google_place():
    return VerifiedPlace(place_id="places/abc", address="Calle Mayor 1, Madrid")


class FakePlaceSearchService(PlaceSearchService):
    def __init__(self, places=None, enabled=True):
        self.places = places or []
        self.enabled = enabled
        self.searches = []

    def is_enabled(self):
        return self.enabled

    def search(self, text, near="", country=""):
        self.searches.append((text, near, country))
        return self.places

    def details(self, place_id):
        return next((p for p in self.places if p.place_id == place_id), None)


def tres_hermanas(phone="+34 912 345 678"):
    return FoundPlace(place_id="places/tres", name="Pizzería Tres Hermanas", phone=phone, address="Calle Luna 3, Madrid")


def biergarten():
    return FoundPlace(place_id="places/bier", name="Augustiner Bräustuben", phone="+49 89 507047", address="Landsberger Str. 19, München")
