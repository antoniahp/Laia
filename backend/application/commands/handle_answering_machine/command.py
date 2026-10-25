import logging

from domain.entities import Order

logger = logging.getLogger(__name__)


class HandleAnsweringMachineCommand:
    """Si contesta un contestador automático, Laia cuelga y te avisa."""

    def __init__(self, call_service, live_calls):
        self.call_service = call_service
        self.live_calls = live_calls

    def execute(self, dto):
        call = self.live_calls.get(dto.order_id)
        if not call or not (dto.answered_by.startswith("machine") or dto.answered_by == "fax"):
            return
        try:
            self.call_service.hang_up(dto.call_id or call.order.call_sid)
        except Exception as error:  # noqa: BLE001
            logger.warning("No se pudo colgar el contestador: %s", error)
        call.log("Ha saltado un contestador automático. Laia ha colgado.")
        call.set_status(Order.FAILED)
        call.flush()
