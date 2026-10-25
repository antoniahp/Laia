from ninja import Router

from application.commands.register_account.command import RegisterAccountCommand
from application.commands.register_account.command_dto import RegisterAccountCommandDTO
from application.queries.authenticate_token.query import AuthenticateTokenQuery
from application.queries.authenticate_token.query_dto import AuthenticateTokenQueryDTO
from infrastructure import dependencies
from infrastructure.api.auth_register.schema import RegisterSchema
from infrastructure.api.shared.schemas import TokenSchema

router = Router(tags=["cuentas"])


@router.post("/auth/register", response=TokenSchema, auth=None)
def register(request, data: RegisterSchema):
    repositories, tokens = dependencies.get_repositories(), dependencies.get_token_service()
    token = RegisterAccountCommand(repositories, tokens).execute(RegisterAccountCommandDTO(**data.dict()))
    account = AuthenticateTokenQuery(repositories, tokens).execute(AuthenticateTokenQueryDTO(token=token))
    return {"token": token, "user": account}
