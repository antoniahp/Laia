import pytest

from domain.entities import Account
from domain.exceptions import CallInProgress, CountryNotAllowed, DailyLimitReached, InvalidPhone, PremiumRateNumber
from domain.rules.answers import is_no, is_yes
from domain.rules.call_policy import ensure_can_call
from domain.rules.phone_format import parse_callable_phone, same_phone


def test_phone_is_normalized_to_international_format():
    phone = parse_callable_phone("612 345 678", ["ES"])
    assert phone.e164 == "+34612345678"
    assert phone.country == "ES"


def test_premium_rate_numbers_are_never_called():
    with pytest.raises(PremiumRateNumber):
        parse_callable_phone("+34 806 123 456", ["ES"])


def test_countries_outside_the_list_are_blocked():
    with pytest.raises(CountryNotAllowed):
        parse_callable_phone("+1 212 555 0100", ["ES"])


def test_rubbish_is_not_a_phone():
    with pytest.raises(InvalidPhone):
        parse_callable_phone("hola", ["ES"])


def test_same_phone_ignores_format():
    assert same_phone("+34 612 34 56 78", "612345678")


def test_short_answers():
    assert is_yes("Sí, vale") and is_yes("ok")
    assert is_no("nada") and is_no(None)
    assert not is_yes("no")


def test_daily_limit_and_one_call_at_a_time():
    account = Account(email="a@b.com")
    ensure_can_call(account, calls_today=1, has_call_in_progress=False, max_calls_per_day=2)
    with pytest.raises(DailyLimitReached):
        ensure_can_call(account, calls_today=2, has_call_in_progress=False, max_calls_per_day=2)
    with pytest.raises(CallInProgress):
        ensure_can_call(account, calls_today=0, has_call_in_progress=True, max_calls_per_day=2)


def test_admins_have_no_daily_limit():
    ensure_can_call(Account(email="a@b.com", is_admin=True), calls_today=99, has_call_in_progress=False, max_calls_per_day=2)
