"""Escuchar la llamada en directo, con websockets de verdad."""

import base64
import json

import pytest
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from application.shared.live_audio import LiveAudioHub
from application.shared.live_calls import Customer, LiveCall, LiveCallRegistry
from domain.entities import Account, Business, Order
from infrastructure import dependencies
from infrastructure.services.jwt_token_service import JwtTokenService
from infrastructure.voice import listen_websocket
from infrastructure.voice.listen_websocket import app_listen_websocket, twilio_listen_websocket


@pytest.fixture
def setup(transactional_db, monkeypatch, message_service):
    account = Account(email="marta@laia.dev", name="Marta", address="Calle Mayor 12")
    account.set_password("12345678")
    account.save()
    other = Account(email="otra@laia.dev")
    other.set_password("12345678")
    other.save()
    business = Business.objects.create(name="Tres Hermanas", phone="+34612345678", country="ES", status=Business.VERIFIED)
    order = Order.objects.create(account=account, business=business, business_name="Tres Hermanas", language="es", items=["x"])

    registry, hub = LiveCallRegistry(), LiveAudioHub()
    registry.add(LiveCall(order, Customer("Marta", "", ""), None, dependencies.get_repositories(), message_service))
    monkeypatch.setattr(dependencies, "get_live_calls", lambda: registry)
    monkeypatch.setattr(dependencies, "get_live_audio", lambda: hub)
    monkeypatch.setattr(listen_websocket, "CHECK_EVERY_SECONDS", 0.05)
    tokens = JwtTokenService()
    app = Starlette(
        routes=[
            WebSocketRoute("/ws/listen", twilio_listen_websocket),
            WebSocketRoute("/ws/app/listen/{order_id}", app_listen_websocket),
        ]
    )
    return {
        "client": TestClient(app),
        "order": order,
        "hub": hub,
        "registry": registry,
        "token": tokens.issue(str(account.id)),
        "other_token": tokens.issue(str(other.id)),
    }


def twilio_message(event, **data):
    return json.dumps({"event": event, **data})


def test_only_the_owner_can_listen(setup):
    client, order = setup["client"], setup["order"]
    for headers in ({}, {"Authorization": f"Bearer {setup['other_token']}"}):
        with pytest.raises(WebSocketDisconnect) as closed:
            with client.websocket_connect(f"/ws/app/listen/{order.id}", headers=headers) as ws:
                ws.receive_bytes()
        assert closed.value.code == 4403


def test_owner_hears_the_mixed_call(setup):
    client, order, hub = setup["client"], setup["order"], setup["hub"]
    headers = {"Authorization": f"Bearer {setup['token']}"}
    with client.websocket_connect(f"/ws/app/listen/{order.id}", headers=headers) as app_ws:
        with client.websocket_connect("/ws/listen") as twilio_ws:
            twilio_ws.send_text(twilio_message("connected"))
            twilio_ws.send_text(
                twilio_message("start", start={"customParameters": {"order_id": str(order.id), "secret": order.call_secret}})
            )
            payload = base64.b64encode(b"\xff" * 160).decode()
            for ms in range(0, 200, 20):
                for track in ("inbound", "outbound"):
                    twilio_ws.send_text(twilio_message("media", media={"track": track, "timestamp": str(ms), "payload": payload}))
            twilio_ws.send_text(twilio_message("stop"))
        received = b""
        while len(received) < 10 * 320:
            received += app_ws.receive_bytes()
        assert len(received) == 10 * 320
    assert hub._channels == {}


def test_twilio_stream_with_wrong_secret_is_ignored(setup):
    client, order, hub = setup["client"], setup["order"], setup["hub"]
    with client.websocket_connect("/ws/listen") as twilio_ws:
        twilio_ws.send_text(twilio_message("start", start={"customParameters": {"order_id": str(order.id), "secret": "mal"}}))
        with pytest.raises(WebSocketDisconnect):
            twilio_ws.receive_text()
    assert hub._channels == {}


def test_listener_leaves_when_the_call_ends_without_audio(setup):
    client, order, registry = setup["client"], setup["order"], setup["registry"]
    headers = {"Authorization": f"Bearer {setup['token']}"}
    with client.websocket_connect(f"/ws/app/listen/{order.id}", headers=headers) as app_ws:
        registry.remove(order.id)
        with pytest.raises(WebSocketDisconnect):
            app_ws.receive_bytes()
    assert setup["hub"]._channels == {}
