from ninja import Schema


class FindPlacesSchema(Schema):
    search: str
    country: str = ""


class AddGoogleBusinessSchema(Schema):
    google_place_id: str
    label: str = ""


class ProposeBusinessSchema(Schema):
    name: str
    phone: str
    language: str = "es"
    city: str = ""
