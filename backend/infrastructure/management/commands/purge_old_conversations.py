from django.conf import settings
from django.core.management.base import BaseCommand

from application.commands.purge_old_conversations.command import PurgeOldConversationsCommand
from application.commands.purge_old_conversations.command_dto import PurgeOldConversationsCommandDTO
from infrastructure import dependencies


class Command(BaseCommand):
    help = "Borra las conversaciones de los pedidos con más de RETENTION_DAYS días (solo queda el resultado)."

    def handle(self, *args, **options):
        days = settings.LAIA["RETENTION_DAYS"]
        count = PurgeOldConversationsCommand(dependencies.get_repositories()).execute(PurgeOldConversationsCommandDTO(days=days))
        self.stdout.write(f"Conversaciones borradas: {count} (más de {days} días).")
