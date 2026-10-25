from dataclasses import dataclass


@dataclass(frozen=True)
class HandleTelegramButtonCommandDTO:
    chat_id: int
    message_id: int
    callback_id: str
    data: str
