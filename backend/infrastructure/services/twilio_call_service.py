import logging

from django.conf import settings
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from twilio.twiml.voice_response import Connect, Dial, Start, Stream, VoiceResponse

from domain.services.call_service import CallService

logging.getLogger("twilio.http_client").setLevel(logging.WARNING)

SAY_LANGUAGE = {"es": "es-ES", "en": "en-GB", "de": "de-DE", "fr": "fr-FR", "it": "it-IT", "pt": "pt-PT", "ja": "ja-JP"}


class TwilioCallService(CallService):
    def __init__(self):
        cfg = settings.LAIA
        self.public_url = cfg["PUBLIC_URL"]
        self.from_number = cfg["TWILIO_FROM_NUMBER"]
        self.enable_amd = cfg["ENABLE_AMD"]
        self.validate_signature = cfg["VALIDATE_TWILIO_SIGNATURE"]
        self.client = Client(cfg["TWILIO_ACCOUNT_SID"] or "AC_missing", cfg["TWILIO_AUTH_TOKEN"] or "missing")
        self.validator = RequestValidator(cfg["TWILIO_AUTH_TOKEN"])

    def _ws(self, path):
        return self.public_url.replace("https://", "wss://").replace("http://", "ws://") + path

    def call_twiml(self, order_id, secret):
        """Al contestar: una copia del audio va a /ws/listen (para escuchar en la app) y la llamada a /ws (Laia)."""
        response = VoiceResponse()
        start = Start()
        listen = Stream(url=self._ws("/ws/listen"), track="both_tracks")
        listen.parameter(name="order_id", value=order_id)
        listen.parameter(name="secret", value=secret)
        start.append(listen)
        response.append(start)

        connect = Connect()
        agent = Stream(url=self._ws("/ws"))
        agent.parameter(name="order_id", value=order_id)
        agent.parameter(name="secret", value=secret)
        connect.append(agent)
        response.append(connect)
        return str(response)

    def place_call(self, to, order_id, secret, ivr_digits=""):
        args = {
            "to": to,
            "from_": self.from_number,
            "twiml": self.call_twiml(order_id, secret),
            "status_callback": f"{self.public_url}/twilio/status/{order_id}",
            "status_callback_event": ["initiated", "ringing", "answered", "completed"],
            "time_limit": 600,  # máximo 10 minutos
        }
        if ivr_digits:
            args["send_digits"] = ivr_digits
        if self.enable_amd:
            args.update(
                machine_detection="Enable",
                async_amd="true",
                async_amd_status_callback=f"{self.public_url}/twilio/amd/{order_id}",
                async_amd_status_callback_method="POST",
            )
        return self.client.calls.create(**args).sid

    def transfer_twiml(self, to, message, language):
        response = VoiceResponse()
        response.say(message, language=SAY_LANGUAGE.get(language, "en-GB"))
        dial = Dial(caller_id=self.from_number, timeout=30)
        dial.number(to)
        response.append(dial)
        return str(response)

    def transfer(self, call_id, to, message, language):
        self.client.calls(call_id).update(twiml=self.transfer_twiml(to, message, language))

    def hang_up(self, call_id):
        if call_id:
            self.client.calls(call_id).update(status="completed")

    def is_request_authentic(self, url, params, signature):
        if not self.validate_signature:
            return True
        return self.validator.validate(url, params, signature)
