from ninja import Schema


class RegisterSchema(Schema):
    email: str
    password: str
    name: str = ""
    signup_code: str = ""
    accept_terms: bool = False
