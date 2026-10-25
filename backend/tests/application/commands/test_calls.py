import asyncio
from types import SimpleNamespace

import pytest

from application.commands.answer_question.command import AnswerQuestionCommand
from application.commands.answer_question.command_dto import AnswerQuestionCommandDTO
from application.commands.handle_answering_machine.command import HandleAnsweringMachineCommand
from application.commands.handle_answering_machine.command_dto import HandleAnsweringMachineCommandDTO
from application.commands.hang_up.command import HangUpCommand
from application.commands.hang_up.command_dto import HangUpCommandDTO
from application.commands.place_order.command import PlaceOrderCommand
from application.commands.place_order.command_dto import PlaceOrderCommandDTO
from application.commands.record_call_status.command import RecordCallStatusCommand
from application.commands.record_call_status.command_dto import RecordCallStatusCommandDTO
from application.shared.live_calls import Customer, LiveCall, run_now
from domain.entities import Business, Order
from domain.exceptions import BusinessNotVerified, CallInProgress, CallNotPlaced, DailyLimitReached, NotWaitingForAnswer
from tests.fakes import FakeCallService


def place(repositories, call_service, message_service, live_calls, account, business, **data):
    command = PlaceOrderCommand(repositories, call_service, message_service, live_calls, run_now)
    data.setdefault("items", ["pizza cuatro quesos"])
    return command.execute(PlaceOrderCommandDTO(account_id=account.id, business_id=business.id, **data))


def test_place_order_calls_the_business_with_a_secret(repositories, call_service, message_service, live_calls, account, pizzeria):
    pizzeria.set_ivr_digits("ww1")
    pizzeria.save()
    order = place(repositories, call_service, message_service, live_calls, account, pizzeria, max_price=20)
    order.refresh_from_db()
    assert order.status == Order.CALLING
    assert order.call_sid == "CA1"
    call = call_service.calls[0]
    assert call["to"] == "+34612345678" and call["secret"] == order.call_secret and call["ivr_digits"] == "ww1"
    assert live_calls.get(order.id) is not None


def test_one_call_at_a_time_and_daily_limit(repositories, call_service, message_service, live_calls, account, pizzeria):
    first = place(repositories, call_service, message_service, live_calls, account, pizzeria)
    with pytest.raises(CallInProgress):
        place(repositories, call_service, message_service, live_calls, account, pizzeria)
    RecordCallStatusCommand(live_calls).execute(RecordCallStatusCommandDTO(order_id=str(first.id), call_status="no-answer"))
    place(repositories, call_service, message_service, live_calls, account, pizzeria)
    live_calls.clear()
    with pytest.raises(DailyLimitReached):
        place(repositories, call_service, message_service, live_calls, account, pizzeria)


def test_pending_businesses_are_never_called(repositories, call_service, message_service, live_calls, account, pizzeria):
    pizzeria.status = Business.PENDING
    pizzeria.save()
    with pytest.raises(BusinessNotVerified):
        place(repositories, call_service, message_service, live_calls, account, pizzeria)
    assert call_service.calls == []


def test_if_twilio_fails_the_order_is_marked_failed(repositories, message_service, live_calls, account, pizzeria):
    with pytest.raises(CallNotPlaced):
        place(repositories, FakeCallService(fail=True), message_service, live_calls, account, pizzeria)
    assert Order.objects.get().status == Order.FAILED
    assert "⚠️" in message_service.sent[-1]["text"]


def test_no_answer_finishes_the_call_and_tells_the_user(repositories, call_service, message_service, live_calls, account, pizzeria):
    order = place(repositories, call_service, message_service, live_calls, account, pizzeria)
    RecordCallStatusCommand(live_calls).execute(RecordCallStatusCommandDTO(order_id=str(order.id), call_status="ringing"))
    RecordCallStatusCommand(live_calls).execute(RecordCallStatusCommandDTO(order_id=str(order.id), call_status="no-answer"))
    order.refresh_from_db()
    assert order.status == Order.FAILED
    assert order.events[-2:] == ["Sonando...", "No contestan."]
    assert live_calls.get(order.id) is None
    assert message_service.sent[-1]["chat_id"] == account.telegram_chat_id


def test_answering_machine_hangs_up(repositories, call_service, message_service, live_calls, account, pizzeria):
    order = place(repositories, call_service, message_service, live_calls, account, pizzeria)
    HandleAnsweringMachineCommand(call_service, live_calls).execute(
        HandleAnsweringMachineCommandDTO(order_id=str(order.id), answered_by="machine_start", call_id="CA1")
    )
    order.refresh_from_db()
    assert call_service.hung_up == ["CA1"]
    assert order.status == Order.FAILED


def test_hang_up_cancels(repositories, call_service, message_service, live_calls, account, pizzeria):
    order = place(repositories, call_service, message_service, live_calls, account, pizzeria)
    HangUpCommand(repositories, call_service, live_calls).execute(HangUpCommandDTO(account_id=account.id, order_id=order.id))
    order.refresh_from_db()
    assert order.status == Order.CANCELLED


def test_answer_reaches_laia_while_she_waits(repositories, call_service, message_service, live_calls, account, pizzeria):
    order = place(repositories, call_service, message_service, live_calls, account, pizzeria)
    with pytest.raises(NotWaitingForAnswer):
        AnswerQuestionCommand(repositories, live_calls).execute(
            AnswerQuestionCommandDTO(account_id=account.id, order_id=order.id, answer="Sí")
        )

    # Dentro de la llamada (bucle asíncrono) los cambios se guardan en otro hilo; aquí, en memoria
    saved = []
    in_memory = SimpleNamespace(orders=SimpleNamespace(save=lambda o, fields=None: saved.append(list(o.events))))
    call = LiveCall(order, Customer("Marta", "", ""), account.telegram_chat_id, in_memory, message_service)

    async def conversation():
        waiting = asyncio.create_task(call.ask_user("No hay cuatro quesos. ¿Margarita?", timeout=5))
        await asyncio.sleep(0.01)
        assert call.order.status == Order.WAITING_USER
        assert message_service.sent[-1]["buttons"][0][0] == ("Sí", f"a|{order.id}|Sí")
        assert call.answer("Sí")
        return await waiting

    assert asyncio.run(conversation()) == "Sí"
    assert call.order.pending_question is None
    assert call.order.status == Order.CALLING
    assert "Respondiste: Sí" in saved[-1]


def test_orders_never_stay_stuck_when_the_call_dies(repositories, call_service, message_service, live_calls, account, pizzeria):
    order = place(repositories, call_service, message_service, live_calls, account, pizzeria)
    live_calls.clear()  # la llamada se cayó: ya no está en memoria
    RecordCallStatusCommand(live_calls, repositories).execute(RecordCallStatusCommandDTO(order_id=str(order.id), call_status="completed"))
    order.refresh_from_db()
    assert order.status == Order.FAILED


def test_hang_up_works_even_without_live_call(repositories, call_service, message_service, live_calls, account, pizzeria):
    order = place(repositories, call_service, message_service, live_calls, account, pizzeria)
    live_calls.clear()
    HangUpCommand(repositories, call_service, live_calls).execute(HangUpCommandDTO(account_id=account.id, order_id=order.id))
    order.refresh_from_db()
    assert order.status == Order.CANCELLED
