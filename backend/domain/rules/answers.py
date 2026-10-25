"""Cómo entiende Laia las respuestas cortas del usuario ("sí", "vale", "nada"...)."""

YES_WORDS = ("s", "y", "vale", "ok", "claro", "venga", "dale")
NO_WORDS = ("nada", "no", "cancela", "cancelar")


def is_yes(answer):
    return bool(answer) and answer.strip().lower().startswith(YES_WORDS)


def is_no(answer):
    return not answer or answer.strip().lower() in NO_WORDS
