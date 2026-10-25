from domain.entities import Order
from domain.exceptions import CallNotActive, CallNotPlaced, MissingCustomerPhone, OrderNotFound
from domain.rules.country_language import TRANSFER_MESSAGE


class TransferCallCommand:
    """«Hablar yo»: Laia avisa al negocio y conecta la llamada con tu móvil. Ella deja de hablar."""

    def __init__(self, repositories, call_service, live_calls):
        self.repositories = repositories
        self.call_service = call_service
        self.live_calls = live_calls

    def execute(self, dto):
        order = self.repositories.orders.find_for_account(dto.account_id, dto.order_id)
        if not order:
            raise OrderNotFound()
        account = self.repositories.accounts.find(dto.account_id)
        if not account.phone:
            raise MissingCustomerPhone()
        call = self.live_calls.get(order.id)
        if not call or call.order.is_finished or not call.order.call_sid:
            raise CallNotActive()

        name = account.name or "la persona que encarga el pedido"
        message = TRANSFER_MESSAGE.get(order.language, TRANSFER_MESSAGE["en"]).format(name=name)
        # Primero el estado final: así el agente no lo marca como fallido al cortarse su audio
        call.order.transfer_to_customer()
        call.set_status(Order.TRANSFERRED)
        try:
            self.call_service.transfer(call.order.call_sid, to=account.phone, message=message, language=order.language)
        except Exception as error:
            call.log("No he podido pasarte la llamada.")
            call.flush()
            raise CallNotPlaced("No he podido pasarte la llamada. Inténtalo otra vez.") from error
        call.flush()
