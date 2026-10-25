import uuid


def valid_uuid(value):
    """Ids que llegan de fuera (URLs, botones): si no son UUID válidos, no existen."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None
