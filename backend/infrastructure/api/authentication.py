from ninja.security import HttpBearer

from application.queries.authenticate_token.query import AuthenticateTokenQuery
from application.queries.authenticate_token.query_dto import AuthenticateTokenQueryDTO
from infrastructure import dependencies


class JwtAuthentication(HttpBearer):
    """Authorization: Bearer <token>. Deja la cuenta en request.auth."""

    def authenticate(self, request, token):
        query = AuthenticateTokenQuery(dependencies.get_repositories(), dependencies.get_token_service())
        return query.execute(AuthenticateTokenQueryDTO(token=token))
