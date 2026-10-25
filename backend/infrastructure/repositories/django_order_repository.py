from domain.entities import Order
from domain.repositories.order_repository import OrderRepository
from infrastructure.repositories._ids import valid_uuid


class DjangoOrderRepository(OrderRepository):
    def find(self, order_id):
        pk = valid_uuid(order_id)
        return Order.objects.filter(pk=pk).first() if pk else None

    def find_for_account(self, account_id, order_id):
        pk = valid_uuid(order_id)
        return Order.objects.filter(pk=pk, account_id=account_id).first() if pk else None

    def save(self, order, fields=None):
        order.save(update_fields=fields) if fields and not order._state.adding else order.save()

    def count_since(self, account_id, since):
        return Order.objects.filter(account_id=account_id, created_at__gte=since).count()

    def list_for_account(self, account_id, limit=50):
        return list(Order.objects.filter(account_id=account_id).order_by("-created_at")[:limit])

    def forget_conversations_before(self, cutoff):
        return (
            Order.objects.filter(created_at__lt=cutoff)
            .exclude(transcript=[], events=[])
            .update(transcript=[], events=[], pending_question=None)
        )
