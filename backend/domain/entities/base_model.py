import uuid

from django.db import models


class BaseModel(models.Model):
    """Todos los modelos del dominio usan un UUID4 como id (no números autoincrementales)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
