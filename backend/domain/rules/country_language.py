"""Idioma en el que Laia habla con un negocio según su país."""

COUNTRY_LANGUAGE = {
    "ES": "es",
    "MX": "es",
    "AR": "es",
    "DE": "de",
    "AT": "de",
    "CH": "de",
    "FR": "fr",
    "BE": "fr",
    "LU": "fr",
    "IT": "it",
    "PT": "pt",
    "BR": "pt",
    "GB": "en",
    "IE": "en",
    "US": "en",
    "NL": "en",
    "JP": "ja",
}

# Para buscar en Google Maps fuera de España
COUNTRY_NAME_EN = {
    "ES": "Spain",
    "DE": "Germany",
    "AT": "Austria",
    "CH": "Switzerland",
    "FR": "France",
    "BE": "Belgium",
    "IT": "Italy",
    "PT": "Portugal",
    "GB": "United Kingdom",
    "IE": "Ireland",
    "NL": "Netherlands",
    "LU": "Luxembourg",
    "JP": "Japan",
}

# Para enseñar en la app
COUNTRY_NAME_ES = {
    "ES": "España",
    "DE": "Alemania",
    "AT": "Austria",
    "CH": "Suiza",
    "FR": "Francia",
    "BE": "Bélgica",
    "IT": "Italia",
    "PT": "Portugal",
    "GB": "Reino Unido",
    "IE": "Irlanda",
    "NL": "Países Bajos",
    "LU": "Luxemburgo",
    "JP": "Japón",
    "MX": "México",
    "AR": "Argentina",
    "BR": "Brasil",
    "US": "Estados Unidos",
}

# Lo que dice Laia al pasarte la llamada, en el idioma del negocio
TRANSFER_MESSAGE = {
    "es": "Un momento, por favor. Le paso con {name}.",
    "en": "One moment, please. I'm putting you through to {name}.",
    "de": "Einen Moment bitte. Ich verbinde Sie mit {name}.",
    "fr": "Un instant, s'il vous plaît. Je vous passe {name}.",
    "it": "Un attimo, per favore. Le passo {name}.",
    "pt": "Um momento, por favor. Vou passar a chamada para {name}.",
    "ja": "少々お待ちください。{name}にお繋ぎします。",
}


def language_for_country(country):
    return COUNTRY_LANGUAGE.get(country, "en")


def country_name(country):
    return COUNTRY_NAME_EN.get(country, country)


def country_name_es(country):
    return COUNTRY_NAME_ES.get(country, country)
