from dataclasses import dataclass


@dataclass(frozen=True)
class HandleTelegramMessageCommandDTO:
    chat_id: int
    text: str
