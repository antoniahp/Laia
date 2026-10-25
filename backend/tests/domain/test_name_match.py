import pytest

from domain.rules.name_match import name_matches


@pytest.mark.parametrize(
    ("query", "name"),
    [
        ("pizzería bebé", "pizzeria bebé"),
        ("Pizzería Bebé de mi agenda", "pizzeria bebé"),
        ("la pizzeria bebe de mis sitios", "Pizzeria Bebé"),
        ("bebé", "pizzeria bebé"),
        ("Tres Hermanas", "Pizzería Tres Hermanas"),
    ],
)
def test_finds_saved_places_whatever_the_accents(query, name):
    assert name_matches(query, name)


@pytest.mark.parametrize(("query", "name"), [("sushi kame", "pizzeria bebé"), ("de mi agenda", "pizzeria bebé")])
def test_does_not_mix_places(query, name):
    assert not name_matches(query, name)
