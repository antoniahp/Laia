from ninja import Router

from application.commands.log_in.command import LogInCommand
from application.commands.log_in.command_dto import LogInCommandDTO
from application.queries.authenticate_token.query import AuthenticateTokenQuery
from application.queries.authenticate_token.query_dto import AuthenticateTokenQueryDTO
from infrastructure import dependencies
from infrastructure.api.auth_login.schema import LoginSchema
from infrastructure.api.shared.schemas import TokenSchema

router = Router(tags=["cuentas"])


@router.post("/auth/login", response=TokenSchema, auth=None)
def login(request, data: LoginSchema):
    repositories, tokens = dependencies.get_repositories(), dependencies.get_token_service()
    token = LogInCommand(repositories, tokens).execute(LogInCommandDTO(**data.dict()))
    account = AuthenticateTokenQuery(repositories, tokens).execute(AuthenticateTokenQueryDTO(token=token))
    return {"token": token, "user": account}
