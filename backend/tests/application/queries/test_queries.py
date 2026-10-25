import pytest

from application.queries.authorize_voice_stream.query import AuthorizeVoiceStreamQuery
from application.queries.authorize_voice_stream.query_dto import AuthorizeVoiceStreamQueryDTO
from application.queries.get_order.query import GetOrderQuery
from application.queries.get_order.query_dto import GetOrderQueryDTO
from application.queries.interpret_order.query import InterpretOrderQuery
from application.queries.interpret_order.query_dto import InterpretOrderQueryDTO
from application.queries.search_businesses.query import SearchBusinessesQuery
from application.queries.search_businesses.query_dto import SearchBusinessesQueryDTO
from application.shared.live_calls import Customer, LiveCall
from domain.entities import Business, Order
from domain.exceptions import BusinessNotVerified, CommandNotUnderstood, LanguageModelUnavailable, OrderNotFound
from tests.fakes import FakeLanguageModelService, pizza_command


def test_search_shows_verified_and_my_own_pending(repositories, account, admin, pizzeria):
    Business.objects.create(name="Mío", phone="+34612000001", country="ES", created_by=account)
    Business.objects.create(name="De otra", phone="+34612000002", country="ES", created_by=admin)
    names = [b.name for b in SearchBusinessesQuery(repositories).execute(SearchBusinessesQueryDTO(account_id=account.id))]
    assert names == ["Mío", "Tres Hermanas"]


def test_interpret_order(repositories, account, pizzeria):
    query = InterpretOrderQuery(repositories, FakeLanguageModelService(pizza_command()))
    parsed, business = query.execute(InterpretOrderQueryDTO(account_id=account.id, business_id=pizzeria.id, command="pide una pizza"))
    assert parsed.alternatives == ["margarita"] and business == pizzeria


def test_interpret_order_without_business_uses_the_name_said(repositories, account):
    query = InterpretOrderQuery(repositories, FakeLanguageModelService(pizza_command(business_name="Tres Hermanas")))
    parsed, business = query.execute(InterpretOrderQueryDTO(account_id=account.id, command="pide una pizza en Tres Hermanas"))
    assert business is None and parsed.business_name == "Tres Hermanas"


def test_interpret_order_needs_a_place(repositories, account):
    with pytest.raises(CommandNotUnderstood):
        InterpretOrderQuery(repositories, FakeLanguageModelService(pizza_command())).execute(
            InterpretOrderQueryDTO(account_id=account.id, command="pide una pizza")
        )


def test_interpret_order_when_the_model_is_down(repositories, account, pizzeria):
    with pytest.raises(LanguageModelUnavailable):
        InterpretOrderQuery(repositories, FakeLanguageModelService()).execute(
            InterpretOrderQueryDTO(account_id=account.id, business_id=pizzeria.id, command="pide una pizza")
        )


def test_interpret_order_refuses_pending_businesses(repositories, account, pizzeria):
    pizzeria.status = Business.PENDING
    pizzeria.save()
    with pytest.raises(BusinessNotVerified):
        InterpretOrderQuery(repositories, FakeLanguageModelService(pizza_command())).execute(
            InterpretOrderQueryDTO(account_id=account.id, business_id=pizzeria.id, command="pide una pizza")
        )


def test_nobody_sees_other_peoples_orders(repositories, account, admin, pizzeria):
    order = Order.prepare(account, pizzeria, "pedido", ["pizza"], [], None, "", False)
    order.save()
    with pytest.raises(OrderNotFound):
        GetOrderQuery(repositories).execute(GetOrderQueryDTO(account_id=admin.id, order_id=order.id))


def test_voice_stream_needs_the_secret(repositories, message_service, live_calls, account, pizzeria):
    order = Order.prepare(account, pizzeria, "pedido", ["pizza"], [], None, "", False)
    order.save()
    live_calls.add(LiveCall(order, Customer("Marta", "", ""), None, repositories, message_service))
    query = AuthorizeVoiceStreamQuery(repositories, live_calls)
    assert query.execute(AuthorizeVoiceStreamQueryDTO(order_id=str(order.id), secret="mal")) is None
    assert query.execute(AuthorizeVoiceStreamQueryDTO(order_id=str(order.id), secret=order.call_secret)) is not None
