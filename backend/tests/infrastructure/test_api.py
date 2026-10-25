"""La API completa, con la base de datos real y los servicios externos falsos."""

import json

import pytest
from django.test import Client

from domain.entities import Business
from infrastructure import dependencies
from tests.fakes import (
    FakeCallService,
    FakeLanguageModelService,
    FakeMessageService,
    FakePlaceSearchService,
    FakeVerificationService,
    pizza_command,
    tres_hermanas,
)


@pytest.fixture
def fakes(monkeypatch, live_calls):
    fake = {
        "calls": FakeCallService(),
        "messages": FakeMessageService(),
    }
    monkeypatch.setattr(dependencies, "get_call_service", lambda: fake["calls"])
    monkeypatch.setattr(dependencies, "get_message_service", lambda: fake["messages"])
    monkeypatch.setattr(dependencies, "get_verification_service", lambda: FakeVerificationService())
    monkeypatch.setattr(dependencies, "get_language_model_service", lambda: FakeLanguageModelService(pizza_command()))
    monkeypatch.setattr(dependencies, "get_place_search_service", lambda: FakePlaceSearchService([tres_hermanas()]))
    monkeypatch.setattr(dependencies, "get_live_calls", lambda: live_calls)
    monkeypatch.setattr(dependencies, "get_background_runner", lambda: lambda fn: fn())
    return fake


@pytest.fixture
def client():
    return Client()


def post(client, url, data=None, token=None):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
    return client.post(url, json.dumps(data or {}), content_type="application/json", **headers)


def signup(client, email="marta@laia.dev"):
    response = post(client, "/api/auth/register", {"email": email, "password": "12345678", "name": "Marta", "accept_terms": True})
    assert response.status_code == 200, response.content
    return response.json()["token"]


def test_full_flow(client, fakes, db):
    admin_token = signup(client, "admin@laia.dev")
    token = signup(client)

    assert client.get("/api/me").status_code == 401
    me = client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {token}").json()
    assert me["telegram_linked"] is False and me["is_admin"] is False

    # Propone un negocio: queda pendiente y no se puede usar
    business = post(client, "/api/businesses", {"name": "Tres Hermanas", "phone": "612 345 678"}, token).json()
    assert business["status"] == "pendiente"
    assert post(client, "/api/parse", {"command": "pide una pizza", "business_id": business["id"]}, token).status_code == 403

    # La administradora lo verifica
    assert client.get("/api/admin/businesses", HTTP_AUTHORIZATION=f"Bearer {token}").status_code == 403
    pending = client.get("/api/admin/businesses", HTTP_AUTHORIZATION=f"Bearer {admin_token}").json()
    assert pending[0]["id"] == business["id"]
    reviewed = post(client, f"/api/admin/businesses/{business['id']}", {"status": "verificado"}, admin_token).json()
    assert reviewed["status"] == "verificado"

    # Interpreta la orden y llama
    draft = post(client, "/api/parse", {"command": "pide una pizza", "business_id": business["id"]}, token).json()
    assert draft["items"] == ["pizza cuatro quesos"] and draft["business"]["name"] == "Tres Hermanas"
    body = {"business_id": business["id"], "items": draft["items"], "alternatives": draft["alternatives"], "max_price": 20}
    assert post(client, "/api/orders", body, token).json()["detail"].startswith("Falta tu dirección")

    response = client.patch(
        "/api/me", json.dumps({"address": "Calle Mayor 12"}), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert response.json()["address"] == "Calle Mayor 12"
    order = post(client, "/api/orders", body, token).json()
    assert order["status"] == "llamando" and fakes["calls"].calls[0]["to"] == "+34612345678"

    # Twilio avisa de que no contestan
    assert client.post(f"/twilio/status/{order['id']}", {"CallStatus": "no-answer"}).status_code == 200
    detail = client.get(f"/api/orders/{order['id']}", HTTP_AUTHORIZATION=f"Bearer {token}").json()
    assert detail["status"] == "fallido" and detail["language_name"] == "español"
    assert len(client.get("/api/orders", HTTP_AUTHORIZATION=f"Bearer {token}").json()) == 1

    # Nadie ve pedidos ajenos
    assert client.get(f"/api/orders/{order['id']}", HTTP_AUTHORIZATION=f"Bearer {admin_token}").status_code == 404


def test_twilio_signature_is_checked(client, fakes, monkeypatch, db):
    monkeypatch.setattr(dependencies, "get_call_service", lambda: FakeCallService(authentic=False))
    assert client.post("/twilio/status/x", {"CallStatus": "ringing"}).status_code == 403


def test_telegram_secret_is_checked(client, fakes, db):
    assert client.post("/telegram/webhook", "{}", content_type="application/json").status_code == 403
    ok = client.post("/telegram/webhook", "{}", content_type="application/json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="secreto")
    assert ok.status_code == 200


def test_validation_errors_are_clear(client, fakes, db):
    response = post(client, "/api/auth/register", {"email": "no-es-email", "password": "12345678", "accept_terms": True})
    assert response.status_code == 400 and response.json()["detail"] == "Ese email no es válido."


def test_say_the_place_and_laia_finds_it(client, fakes, monkeypatch, db):
    monkeypatch.setattr(
        dependencies, "get_language_model_service", lambda: FakeLanguageModelService(pizza_command(business_name="Tres Hermanas"))
    )
    token = signup(client)
    draft = post(client, "/api/parse", {"command": "pide una pizza en Tres Hermanas"}, token).json()
    assert draft["business"] is None and draft["business_name"] == "Tres Hermanas"
    found = post(client, "/api/places/search", {"search": draft["business_name"]}, token).json()
    assert found[0]["name"] == "Pizzería Tres Hermanas" and found[0]["from_google"] is True
    assert Business.objects.count() == 0  # buscar no guarda nada de Google

    added = post(client, "/api/places/add", {"google_place_id": "places/tres", "label": "Tres Hermanas"}, token).json()
    assert added["name"] == "Tres Hermanas" and added["status"] == "verificado" and added["source"] == "google"
    business = Business.objects.get()
    assert business.phone is None and business.address == ""  # solo el place_id

    client.patch(
        "/api/me",
        json.dumps({"address": "Calle Mayor 12, Madrid"}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    order = post(client, "/api/orders", {"business_id": added["id"], "items": ["margarita"]}, token).json()
    assert order["status"] == "llamando"
    assert fakes["calls"].calls[0]["to"] == "+34912345678"  # el teléfono se pide a Google al llamar


def test_legal_pages_are_public(client, db):
    for page in ("privacidad", "terminos", "negocios"):
        response = client.get(f"/legal/{page}/")
        assert response.status_code == 200
        assert "Laia" in response.content.decode()
    assert client.get("/legal/otra/").status_code == 404
    info = client.get("/api/legal").json()
    assert info["terms_version"] == "2026-10" and info["privacy_url"].endswith("/legal/privacidad/")


def test_register_without_accepting_terms_fails(client, fakes, db):
    response = post(client, "/api/auth/register", {"email": "x@y.com", "password": "12345678"})
    assert response.status_code == 400


def test_export_and_delete_my_account(client, fakes, db):
    token = signup(client)
    auth = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    data = client.get("/api/me/export", **auth).json()
    assert data["cuenta"]["email"] == "marta@laia.dev" and data["pedidos"] == []
    assert client.delete("/api/me", **auth).status_code == 204
    assert client.get("/api/me", **auth).status_code == 401


def test_countries_for_calls_abroad(client, fakes, db):
    token = signup(client)
    countries = client.get("/api/places/countries", HTTP_AUTHORIZATION=f"Bearer {token}").json()
    assert countries[0]["code"] == "ES"
    assert {"code": "DE", "name": "Alemania", "language": "de", "language_name": "alemán"} in countries
