import logging

from ninja.errors import AuthenticationError

from domain.exceptions import DomainError
from infrastructure.api.messages_en import in_language

logger = logging.getLogger(__name__)


def register_exception_handlers(api):
    """Convierte los errores de negocio en respuestas claras para la app: {"detail": "..."}."""

    @api.exception_handler(DomainError)
    def domain_error(request, exc):
        logger.info("%s %s -> %s", request.method, request.path, exc)
        return api.create_response(request, {"detail": in_language(request, str(exc))}, status=exc.status_code)

    @api.exception_handler(AuthenticationError)
    def authentication_error(request, exc):
        return api.create_response(request, {"detail": in_language(request, "Inicia sesión.")}, status=401)
