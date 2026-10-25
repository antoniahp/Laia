from abc import ABC, abstractmethod


class CallService(ABC):
    """Hace y cuelga llamadas de teléfono (Twilio)."""

    @abstractmethod
    def place_call(self, to, order_id, secret, ivr_digits=""):
        """Llama y devuelve el identificador de la llamada. El audio se envía al agente y a quien escuche."""

    @abstractmethod
    def transfer(self, call_id, to, message, language):
        """Dice el mensaje al negocio y conecta la llamada con el teléfono `to` (la persona usuaria)."""

    @abstractmethod
    def hang_up(self, call_id):
        pass

    @abstractmethod
    def is_request_authentic(self, url, params, signature):
        """True si el aviso viene de verdad de la compañía telefónica."""
