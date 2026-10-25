from domain.entities import Order

STATUS_TEXT = {
    "busy": "Comunica. Prueba más tarde.",
    "no-answer": "No contestan.",
    "failed": "La llamada falló.",
    "canceled": "Llamada cancelada.",
}


class RecordCallStatusCommand:
    """La compañía telefónica avisa de cómo va la llamada: sonando, no contestan, terminada..."""

    def __init__(self, live_calls, repositories=None):
        self.live_calls = live_calls
        self.repositories = repositories

    def execute(self, dto):
        call = self.live_calls.get(dto.order_id)
        if not call:
            self._close_orphan(dto)
            return
        if dto.call_status == "ringing":
            call.log("Sonando...")
        elif dto.call_status in STATUS_TEXT:
            self._finish(call, STATUS_TEXT[dto.call_status])
        elif dto.call_status == "completed":
            if call.order.status == Order.CALLING:
                self._finish(call, "La llamada terminó antes de empezar.")
            elif call.order.is_finished:
                call.flush()
                self.live_calls.remove(dto.order_id)

    def _finish(self, call, text):
        if not call.order.is_finished:
            call.log(text)
            call.set_status(Order.FAILED)
            call.flush()
        self.live_calls.remove(call.order.id)

    def _close_orphan(self, dto):
        """La llamada ya no está en memoria (se cayó o se reinició el servidor): que el pedido no se quede colgado."""
        if self.repositories is None or dto.call_status not in (*STATUS_TEXT, "completed"):
            return
        order = self.repositories.orders.find(dto.order_id)
        if not order or order.is_finished:
            return
        order.log(STATUS_TEXT.get(dto.call_status, "La llamada terminó."))
        order.mark(Order.FAILED)
        self.repositories.orders.save(order)
