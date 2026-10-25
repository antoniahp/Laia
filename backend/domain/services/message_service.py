from abc import ABC, abstractmethod


class MessageService(ABC):
    """Envía mensajes al usuario (Telegram)."""

    @abstractmethod
    def is_enabled(self):
        """True si el servicio está configurado."""

    @abstractmethod
    def send(self, chat_id, text, buttons=None):
        """Envía el texto con botones opcionales: filas de (texto, dato). Lanza MessageNotSent si falla."""

    @abstractmethod
    def answer_button(self, callback_id, text=""):
        pass

    @abstractmethod
    def remove_buttons(self, chat_id, message_id):
        pass

    @abstractmethod
    def link_url(self, link_code):
        """Enlace para unir el chat con una cuenta, o None si el bot no está disponible."""
