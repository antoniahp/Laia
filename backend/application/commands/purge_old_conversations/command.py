from datetime import timedelta

from django.utils import timezone


class PurgeOldConversationsCommand:
    """Minimización de datos: pasados X días se borran las conversaciones; solo queda el resultado."""

    def __init__(self, repositories):
        self.repositories = repositories

    def execute(self, dto):
        cutoff = timezone.now() - timedelta(days=dto.days)
        return self.repositories.orders.forget_conversations_before(cutoff)
