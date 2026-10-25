"""Lo que hace a Laia usable de verdad: buscar sitios (también fuera), escuchar, hablar tú, privacidad."""

import asyncio
from datetime import timedelta

import pytest
from django.utils import timezone

from application.commands.add_google_business.command import AddGoogleBusinessCommand
from application.commands.add_google_business.command_dto import AddGoogleBusinessCommandDTO
from application.commands.delete_account.command import DeleteAccountCommand
from application.commands.delete_account.command_dto import DeleteAccountCommandDTO
from application.commands.place_order.command import PlaceOrderCommand
from application.commands.place_order.command_dto import PlaceOrderCommandDTO
from application.commands.purge_old_conversations.command import PurgeOldConversationsCommand
from application.commands.purge_old_conversations.command_dto import PurgeOldConversationsCommandDTO
from application.commands.transfer_call.command import TransferCallCommand
from application.commands.transfer_call.command_dto import TransferCallCommandDTO
from application.queries.find_places.query import FindPlacesQuery
from application.queries.find_places.query_dto import FindPlacesQueryDTO
from application.shared.live_audio import LiveAudioHub
from application.shared.live_calls import run_now
from domain.entities import Account, Business, Order
from domain.exceptions import (
    CallInProgressCannotDelete,
    CallNotActive,
    MissingCustomerPhone,
    PlaceNotFound,
    PlaceSearchNotConfigured,
)
from domain.rules.audio import mix_frames, mulaw_to_pcm16
from domain.services.place_search_service import FoundPlace
from tests.fakes import FakeLanguageModelService, FakePlaceSearchService, biergarten, tres_hermanas


def find(repositories, account, places, search="pizza", country="", enabled=True):
    service = FakePlaceSearchService(places, enabled=enabled)
    return FindPlacesQuery(repositories, service).execute(
        FindPlacesQueryDTO(account_id=account.id, search=search, country=country)
    ), service


# ---------- buscar ----------


def test_search_near_home_does_not_save_anything(repositories, account):
    found, service = find(repositories, account, [tres_hermanas()])
    assert found[0].name == "Pizzería Tres Hermanas" and found[0].from_google
    assert found[0].language == "es" and found[0].business_id is None
    assert service.searches == [("pizza", account.address, "")]
    assert Business.objects.count() == 0


def test_search_abroad_uses_the_country_and_its_language(repositories, account):
    found, service = find(repositories, account, [biergarten(), tres_hermanas()], search="Augustiner", country="de")
    assert [p.name for p in found] == ["Augustiner Bräustuben"]  # el español no es de Alemania
    assert found[0].country == "DE" and found[0].language == "de"
    assert service.searches == [("Augustiner", "", "DE")]


def test_numbers_laia_never_calls_are_hidden(repositories, account):
    tarot = FoundPlace(place_id="places/x", name="Tarot", phone="+34 806 123 456", address="")
    usa = FoundPlace(place_id="places/y", name="Joe's", phone="+1 212 555 0100", address="")
    with pytest.raises(PlaceNotFound):
        find(repositories, account, [tarot, usa])


def test_directory_first_and_no_duplicates(repositories, account, pizzeria):
    pizzeria.google_place_id = "places/tres"
    pizzeria.save()
    found, _ = find(repositories, account, [tres_hermanas()], search="Tres")
    assert len(found) == 1 and found[0].business_id == str(pizzeria.id)


def test_without_google_only_the_directory(repositories, account, pizzeria):
    found, _ = find(repositories, account, [], search="Tres", enabled=False)
    assert found[0].name == "Tres Hermanas"
    with pytest.raises(PlaceSearchNotConfigured):
        find(repositories, account, [], search="nada", enabled=False)


def test_rejected_google_places_stay_hidden(repositories, account):
    Business.objects.create(name="X", source=Business.GOOGLE, google_place_id="places/tres", country="ES", status=Business.REJECTED)
    with pytest.raises(PlaceNotFound):
        find(repositories, account, [tres_hermanas()])


# ---------- llamar a un sitio de Google ----------


def add_google(repositories, account, place, label=""):
    return AddGoogleBusinessCommand(repositories, FakePlaceSearchService([place])).execute(
        AddGoogleBusinessCommandDTO(account_id=account.id, google_place_id=place.place_id, label=label)
    )


def test_abroad_order_calls_in_german_and_translates(repositories, call_service, message_service, live_calls, account):
    business = add_google(repositories, account, biergarten(), label="Augustiner")
    assert business.language == "de" and business.phone is None and business.is_verified
    # elegirlo dos veces no lo duplica
    assert add_google(repositories, account, biergarten()).id == business.id

    translator = FakeLanguageModelService(translations={"Was möchten Sie?": "¿Qué desea?"})
    order = PlaceOrderCommand(
        repositories, call_service, message_service, live_calls, run_now, FakePlaceSearchService([biergarten()]), translator
    ).execute(PlaceOrderCommandDTO(account_id=account.id, business_id=business.id, items=["Brezel"]))
    assert call_service.calls[0]["to"] == "+4989507047"
    assert order.language == "de"

    call = live_calls.get(order.id)
    call.add_line("negocio", "Was möchten Sie?")
    order.refresh_from_db()
    assert order.transcript[-1] == {"who": "negocio", "text": "Was möchten Sie?", "tr": "¿Qué desea?"}


# ---------- «Hablar yo» ----------


def start_call(repositories, call_service, message_service, live_calls, account, business):
    order = PlaceOrderCommand(repositories, call_service, message_service, live_calls, run_now).execute(
        PlaceOrderCommandDTO(account_id=account.id, business_id=business.id, items=["margarita"])
    )
    return order


def transfer(repositories, call_service, live_calls, account, order):
    TransferCallCommand(repositories, call_service, live_calls).execute(TransferCallCommandDTO(account_id=account.id, order_id=order.id))


def test_talk_myself_needs_my_phone_and_an_active_call(repositories, call_service, message_service, live_calls, account, pizzeria):
    order = start_call(repositories, call_service, message_service, live_calls, account, pizzeria)
    with pytest.raises(MissingCustomerPhone):
        transfer(repositories, call_service, live_calls, account, order)

    Account.objects.filter(id=account.id).update(phone="+34600111222")
    transfer(repositories, call_service, live_calls, account, order)
    sent = call_service.transfers[0]
    assert sent["call_id"] == "CA1" and sent["to"] == "+34600111222" and "Marta" in sent["message"]
    order.refresh_from_db()
    assert order.status == Order.TRANSFERRED
    assert "pasado la llamada" in message_service.sent[-1]["text"]

    live_calls.clear()
    with pytest.raises(CallNotActive):
        transfer(repositories, call_service, live_calls, account, order)


# ---------- privacidad ----------


def test_old_conversations_are_forgotten_but_the_result_stays(repositories, account, pizzeria):
    old = Order.objects.create(
        account=account,
        business=pizzeria,
        business_name="Tres Hermanas",
        language="es",
        items=["x"],
        transcript=[{"who": "negocio", "text": "Hola"}],
        events=["Llamando"],
        result={"summary": "Margarita 11 €"},
    )
    Order.objects.filter(id=old.id).update(created_at=timezone.now() - timedelta(days=31))
    recent = Order.objects.create(
        account=account,
        business=pizzeria,
        business_name="Tres Hermanas",
        language="es",
        items=["x"],
        transcript=[{"who": "negocio", "text": "Hola"}],
    )
    assert PurgeOldConversationsCommand(repositories).execute(PurgeOldConversationsCommandDTO(days=30)) == 1
    old.refresh_from_db()
    recent.refresh_from_db()
    assert old.transcript == [] and old.events == [] and old.result == {"summary": "Margarita 11 €"}
    assert recent.transcript


def test_delete_account_waits_for_the_call_and_then_erases_everything(
    repositories, call_service, message_service, live_calls, account, pizzeria
):
    start_call(repositories, call_service, message_service, live_calls, account, pizzeria)
    with pytest.raises(CallInProgressCannotDelete):
        DeleteAccountCommand(repositories, live_calls).execute(DeleteAccountCommandDTO(account_id=account.id))
    live_calls.clear()
    DeleteAccountCommand(repositories, live_calls).execute(DeleteAccountCommandDTO(account_id=account.id))
    assert not Account.objects.filter(id=account.id).exists()
    assert Order.objects.count() == 0
    assert Business.objects.filter(id=pizzeria.id).exists()  # el negocio es del directorio, no de la persona


# ---------- escuchar en directo ----------


def test_mulaw_decoding_and_mixing():
    silence = mulaw_to_pcm16(b"\xff" * 160)
    assert len(silence) == 320 and set(silence) == {0}
    loud = mulaw_to_pcm16(b"\x00" * 160)
    assert int.from_bytes(loud[:2], "little", signed=True) == -32124
    mixed = mix_frames([loud, loud])
    assert int.from_bytes(mixed[:2], "little", signed=True) == -32768  # se recorta, no desborda
    assert mix_frames([silence]) == silence


def test_listener_gets_both_sides_mixed_in_order():
    async def scenario():
        hub = LiveAudioHub()
        queue = hub.subscribe("o1")
        channel = hub.channel("o1")
        for ms in range(0, 200, 20):
            channel.add_media("inbound", ms, b"\xff" * 160)
            channel.add_media("outbound", ms, b"\xff" * 160)
        hub.close("o1")
        chunks = []
        while (chunk := await queue.get()) is not None:
            chunks.append(chunk)
        return b"".join(chunks)

    audio = asyncio.run(scenario())
    assert len(audio) == 10 * 320  # 10 tramas de 20 ms a 8 kHz, sin duplicar pistas
