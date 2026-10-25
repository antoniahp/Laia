import pytest

from domain.entities import Account, Business, Order
from domain.exceptions import BusinessNotVerified, EmptyOrder, InvalidIvrDigits, MissingAddress, WeakPassword


def business(status=Business.VERIFIED):
    return Business(name="Tres Hermanas", phone="+34612345678", country="ES", status=status)


def customer(address="Calle Mayor 12"):
    return Account(email="m@b.com", address=address)


def prepare(**overrides):
    data = dict(mode="pedido", items=["pizza 4 quesos"], alternatives=["margarita"], max_price=20, notes="", ask_before_alternative=False)
    data.update(overrides)
    return Order.prepare(
        overrides.pop("account", customer()),
        overrides.pop("business", business()),
        **{k: v for k, v in data.items() if k not in ("account", "business")},
    )


def test_passwords_need_eight_characters():
    with pytest.raises(WeakPassword):
        Account(email="a@b.com").set_password("corta")


def test_password_is_hashed():
    account = Account(email="a@b.com")
    account.set_password("12345678")
    assert account.password_hash != "12345678"
    assert account.check_password("12345678")


def test_telegram_link_code_only_works_once():
    account = Account(email="a@b.com")
    code = account.telegram_link_code
    account.link_telegram(555)
    assert account.telegram_chat_id == 555
    assert account.telegram_link_code != code


def test_laia_only_calls_verified_businesses():
    with pytest.raises(BusinessNotVerified):
        prepare(business=business(Business.PENDING))


def test_an_order_needs_something_to_ask_for():
    with pytest.raises(EmptyOrder):
        prepare(items=["  "])


def test_deliveries_need_an_address_but_questions_do_not():
    with pytest.raises(MissingAddress):
        prepare(account=customer(address=""))
    assert prepare(account=customer(address=""), mode="consulta").mode == "consulta"


def test_price_rule_and_alternatives():
    order = prepare()
    assert order.accepts_price(11.5)
    assert not order.accepts_price(24)
    assert order.next_alternative() == "margarita"
    assert order.next_alternative() is None


def test_finished_orders_do_not_go_back():
    order = prepare()
    assert order.mark(Order.DONE)
    assert not order.mark(Order.IN_CALL)
    assert order.status == Order.DONE


def test_ivr_digits_only_accept_keys_and_pauses():
    b = business()
    b.set_ivr_digits("ww1")
    with pytest.raises(InvalidIvrDigits):
        b.set_ivr_digits("1; rm -rf")


def test_bookings_do_not_need_a_delivery_address(db):
    from domain.entities import Account, Business, Order

    account = Account(email="a@b.com")
    business = Business(name="Trattoria", country="IT", language="it", status=Business.VERIFIED)
    order = Order.prepare(account, business, "reserva", ["mesa para 2, viernes 21:00"], [], None, "", False)
    order.confirm("Mesa para 2 el viernes a las 21:00")
    assert order.events[-1].startswith("¡Reserva hecha!")
