from types import SimpleNamespace

from domain import exceptions
from infrastructure.api.messages_en import EN, in_language


def request(lang):
    return SimpleNamespace(headers={"Accept-Language": lang})


def test_every_domain_error_has_english():
    for name in dir(exceptions):
        cls = getattr(exceptions, name)
        if isinstance(cls, type) and issubclass(cls, exceptions.DomainError):
            assert cls.message in EN, cls.__name__


def test_english_only_when_app_is_in_english():
    msg = exceptions.CommandNotUnderstood.message
    assert in_language(request("en"), msg) == "I didn't understand what you want to order."
    assert in_language(request("es"), msg) == msg
    assert in_language(request("en"), "Laia todavía no llama a ese país (US).") == "Laia doesn't call that country yet."
