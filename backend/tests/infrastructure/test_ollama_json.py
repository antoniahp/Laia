import pytest

from infrastructure.services.ollama_language_model_service import extract_json


@pytest.mark.parametrize(
    "message",
    [
        {"content": '{"mode": "pedido"}'},
        {"content": 'Claro:\n```json\n{"mode": "pedido"}\n```'},
        {"content": 'Aquí tienes {"mode": "pedido"} listo'},
        {"content": "", "thinking": 'Pienso... {"mode": "pedido"}'},
    ],
)
def test_extracts_json_wherever_gemma_puts_it(message):
    assert extract_json(message) == {"mode": "pedido"}


def test_no_json_is_an_error():
    with pytest.raises(ValueError):
        extract_json({"content": "no sé"})
