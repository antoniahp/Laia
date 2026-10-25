from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone

from domain.services.token_service import TokenService


class JwtTokenService(TokenService):
    """Sesiones de la app con JWT firmado con la SECRET_KEY de Django. Caducan a los 30 días."""

    DAYS = 30

    def issue(self, account_id):
        payload = {"sub": str(account_id), "exp": timezone.now() + timedelta(days=self.DAYS)}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    def read(self, token):
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])["sub"]
        except (jwt.PyJWTError, KeyError):
            return None
