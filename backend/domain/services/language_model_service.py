from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParsedCommand:
    mode: str
    items: list = field(default_factory=list)
    alternatives: list = field(default_factory=list)
    max_price: float | None = None
    ask_before_alternative: bool = False
    notes: str = ""
    business_name: str = ""  # el sitio al que hay que llamar, si lo dice ("en Tres Hermanas")


class LanguageModelService(ABC):
    """El cerebro open-weight (Gemma vía Ollama)."""

    @abstractmethod
    def translate(self, text, source_language, target_language="es"):
        """Traduce una frase de la conversación. Lanza LanguageModelUnavailable si no responde."""

    @abstractmethod
    def parse_command(self, text):
        """Convierte "pide una pizza..." en ParsedCommand. Lanza LanguageModelUnavailable si no responde."""
