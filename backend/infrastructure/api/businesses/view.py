from django.conf import settings
from ninja import Router, Schema

from application.commands.add_google_business.command import AddGoogleBusinessCommand
from application.commands.add_google_business.command_dto import AddGoogleBusinessCommandDTO
from application.commands.propose_business.command import ProposeBusinessCommand
from application.commands.propose_business.command_dto import ProposeBusinessCommandDTO
from application.queries.find_places.query import FindPlacesQuery
from application.queries.find_places.query_dto import FindPlacesQueryDTO
from application.queries.search_businesses.query import SearchBusinessesQuery
from application.queries.search_businesses.query_dto import SearchBusinessesQueryDTO
from domain.rules.country_language import country_name_es, language_for_country
from domain.rules.languages import language_name
from infrastructure import dependencies
from infrastructure.api.businesses.schema import AddGoogleBusinessSchema, FindPlacesSchema, ProposeBusinessSchema
from infrastructure.api.shared.schemas import BusinessSchema, PlaceCandidateSchema

router = Router(tags=["negocios"])


class CountrySchema(Schema):
    code: str
    name: str
    language: str
    language_name: str


@router.get("/places/countries", response=list[CountrySchema])
def countries(request):
    """Países a los que Laia puede llamar, con el idioma en que hablará."""
    result = []
    for code in settings.LAIA["ALLOWED_COUNTRIES"]:
        language = language_for_country(code)
        result.append({"code": code, "name": country_name_es(code), "language": language, "language_name": language_name(language)})
    return sorted(result, key=lambda c: (c["code"] != "ES", c["name"]))


@router.get("/businesses", response=list[BusinessSchema])
def search_businesses(request, q: str = ""):
    """Tus sitios: los verificados y los que has propuesto."""
    query = SearchBusinessesQuery(dependencies.get_repositories())
    return query.execute(SearchBusinessesQueryDTO(account_id=request.auth.id, search=q))


@router.post("/businesses", response=BusinessSchema)
def propose_business(request, data: ProposeBusinessSchema):
    """Proponer a mano un negocio que no está en Google Maps (lo revisa una administradora)."""
    command = ProposeBusinessCommand(
        dependencies.get_repositories(), dependencies.get_verification_service(), dependencies.get_message_service()
    )
    return command.execute(ProposeBusinessCommandDTO(account_id=request.auth.id, **data.dict()))


@router.post("/places/search", response=list[PlaceCandidateSchema])
def find_places(request, data: FindPlacesSchema):
    """Busca un sitio por nombre: en tu lista y en Google Maps (cerca de ti o en otro país). No guarda nada."""
    query = FindPlacesQuery(dependencies.get_repositories(), dependencies.get_place_search_service())
    return query.execute(FindPlacesQueryDTO(account_id=request.auth.id, search=data.search, country=data.country))


@router.post("/places/add", response=BusinessSchema)
def add_google_business(request, data: AddGoogleBusinessSchema):
    """Guarda en tu lista el sitio de Google Maps que has elegido (solo su identificador)."""
    command = AddGoogleBusinessCommand(dependencies.get_repositories(), dependencies.get_place_search_service())
    return command.execute(AddGoogleBusinessCommandDTO(account_id=request.auth.id, **data.dict()))
