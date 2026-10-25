"""¿El nombre que dices es el de un sitio guardado? Sin tildes, sin mayúsculas y sin palabras de relleno."""

import re
import unicodedata

FILLER = {"de", "del", "en", "a", "al", "la", "el", "los", "las", "mi", "mis", "agenda", "sitio", "sitios", "lista", "contactos"}


def normalize(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    words = re.sub(r"[^a-z0-9 ]", " ", text).split()
    return " ".join(w for w in words if w not in FILLER)


def name_matches(query, name):
    q, n = normalize(query), normalize(name)
    if not q or not n:
        return False
    if q in n or (n in q and len(n) >= 4):
        return True
    words = [w for w in q.split() if len(w) >= 3]
    return bool(words) and all(w in n.split() or w in n for w in words)
