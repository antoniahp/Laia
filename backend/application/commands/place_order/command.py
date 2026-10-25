from datetime import datetime, time

from django.conf import settings
from django.utils import timezone

from application.shared.live_calls import Customer, LiveCall
from domain.entities import Order
from domain.exceptions import BusinessNotFound, CallNotPlaced, PlaceUnavailable, SessionExpired
from domain.rules.call_policy import ensure_can_call
from domain.rules.phone_format import parse_callable_phone


class PlaceOrderCommand:
    """Comprueba las reglas, guarda el pedido y Laia llama al negocio."""

    def __init__(
        self,
        repositories,
        call_service,
        message_service,
        live_calls,
        run_in_background,
        place_search_service=None,
        language_model_service=None,
    ):
        self.repositories = repositories
        self.call_service = call_service
        self.message_service = message_service
        self.live_calls = live_calls
        self.run_in_background = run_in_background
        self.place_search_service = place_search_service
        self.language_model_service = language_model_service

    def execute(self, dto):
        account = self.repositories.accounts.find(dto.account_id)
        if not account:
            raise SessionExpired()
        business = self.repositories.businesses.find(dto.business_id)
        if not business:
            raise BusinessNotFound()

        start_of_day = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
        ensure_can_call(
            account,
            calls_today=self.repositories.orders.count_since(account.id, start_of_day),
            has_call_in_progress=self.live_calls.has_active_call(account.id),
            max_calls_per_day=settings.LAIA["MAX_CALLS_PER_DAY"],
        )

        order = Order.prepare(
            account,
            business,
            mode=dto.mode,
            items=dto.items,
            alternatives=dto.alternatives,
            max_price=dto.max_price,
            notes=dto.notes,
            ask_before_alternative=dto.ask_before_alternative,
        )
        phone = self._phone_of(business)
        self.repositories.orders.save(order)

        call = LiveCall(
            order,
            Customer(account.name, account.address, account.phone),
            account.telegram_chat_id,
            self.repositories,
            self.message_service,
            self.run_in_background,
            translator=self.language_model_service,
        )
        self.live_calls.add(call)

        try:
            call_id = self.call_service.place_call(
                to=phone, order_id=str(order.id), secret=order.call_secret, ivr_digits=business.ivr_digits
            )
        except Exception as error:
            call.log("No se pudo hacer la llamada.")
            call.set_status(Order.FAILED)
            call.flush()
            self.live_calls.remove(order.id)
            raise CallNotPlaced() from error

        call.set_call_id(call_id)
        call.flush()
        return order

    def _phone_of(self, business):
        """Los negocios manuales guardan su teléfono. Los de Google no: se pide a Google ahora."""
        if not business.is_from_google:
            return business.phone
        place = self.place_search_service.details(business.google_place_id) if self.place_search_service else None
        if not place:
            raise PlaceUnavailable()
        return parse_callable_phone(place.phone, settings.LAIA["ALLOWED_COUNTRIES"]).e164
