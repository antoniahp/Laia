"""Idiomas en los que Laia puede hablar con un negocio."""

LANGUAGES = {
    "es": "español",
    "en": "inglés",
    "de": "alemán",
    "fr": "francés",
    "it": "italiano",
    "pt": "portugués",
    "ja": "japonés",
}


def language_name(code):
    return LANGUAGES.get(code, code)
