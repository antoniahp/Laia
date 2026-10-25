from dataclasses import dataclass


@dataclass(frozen=True)
class LogInCommandDTO:
    email: str
    password: str
