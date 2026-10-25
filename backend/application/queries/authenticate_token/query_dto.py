from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticateTokenQueryDTO:
    token: str
