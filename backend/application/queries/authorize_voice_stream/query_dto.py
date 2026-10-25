from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorizeVoiceStreamQueryDTO:
    order_id: str
    secret: str
