from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterAccountCommandDTO:
    email: str
    password: str
    name: str = ""
    signup_code: str = ""
    accept_terms: bool = False
