import logging

from domain.entities import Order
from domain.exceptions import OrderNotFound

logger = logging.getLogger(__name__)


class HangUpCommand:
    def __init__(self, repositories, call_service, live_calls):
        self.repositories = repositories
        self.call_service = call_service
        self.live_calls = live_calls

    def execute(self, dto):
        order = self.repositories.orders.find_for_account(dto.account_id, dto.order_id)
        if not order:
            raise OrderNotFound()
        if order.call_sid:
            try:
                self.call_service.hang_up(order.call_sid)
            except Exception as error:  # noqa: BLE001
                logger.warning("No se pudo colgar %s: %s", order.call_sid, error)
        call = self.live_calls.get(order.id)
        if call and not call.order.is_finished:
            call.log("Has colgado la llamada.")
            call.set_status(Order.CANCELLED)
            call.flush()
        elif not call and not order.is_finished:
            # La llamada ya no está en memoria: igualmente se da por terminada
            order.log("Has colgado la llamada.")
            order.mark(Order.CANCELLED)
            self.repositories.orders.save(order)
