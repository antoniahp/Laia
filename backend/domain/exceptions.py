"""Errores de negocio. La API los convierte en respuestas con un mensaje claro para la persona."""


class DomainError(Exception):
    status_code = 400
    message = "No se ha podido completar la operación."

    def __init__(self, message=None):
        super().__init__(message or self.message)


# ---------- cuentas ----------


class InvalidEmail(DomainError):
    message = "Ese email no es válido."


class WeakPassword(DomainError):
    message = "La contraseña debe tener al menos 8 caracteres."


class WrongSignupCode(DomainError):
    status_code = 403
    message = "Código de invitación incorrecto."


class EmailAlreadyUsed(DomainError):
    status_code = 409
    message = "Ya existe una cuenta con ese email."


class WrongCredentials(DomainError):
    status_code = 401
    message = "Email o contraseña incorrectos."


class SessionExpired(DomainError):
    status_code = 401
    message = "Sesión caducada. Vuelve a entrar."


class TermsNotAccepted(DomainError):
    message = "Para usar Laia tienes que aceptar las condiciones y la política de privacidad."


class CallInProgressCannotDelete(DomainError):
    status_code = 409
    message = "Tienes una llamada en curso. Espera a que termine para borrar tu cuenta."


class NotAdmin(DomainError):
    status_code = 403
    message = "Solo para administradores."


# ---------- teléfonos ----------


class InvalidPhone(DomainError):
    message = "No entiendo ese teléfono. Escríbelo con prefijo, por ejemplo +34 600 111 222."


class CountryNotAllowed(DomainError):
    message = "Laia todavía no llama a ese país."


class PremiumRateNumber(DomainError):
    message = "Laia no llama a números de tarificación especial o de servicios."


# ---------- negocios ----------


class InvalidBusinessData(DomainError):
    message = "Revisa el nombre y el idioma del negocio."


class BusinessNotFound(DomainError):
    status_code = 404
    message = "Negocio no encontrado."


class BusinessRejected(DomainError):
    status_code = 409
    message = "Ese número no está permitido."


class BusinessNotVerified(DomainError):
    status_code = 403
    message = "Laia solo llama a negocios verificados. Este aún está pendiente."


class InvalidReview(DomainError):
    message = "Estado no válido."


class PlaceNotFound(DomainError):
    status_code = 404
    message = "No encuentro ese negocio. Prueba con el nombre y la ciudad, o propónlo a mano."


class PlaceSearchNotConfigured(DomainError):
    status_code = 503
    message = "No encuentro ese negocio en tu lista. Para buscar en Google Maps hay que configurar GOOGLE_PLACES_API_KEY."


class PlaceUnavailable(DomainError):
    status_code = 502
    message = "Google Maps no me da el teléfono de ese negocio ahora mismo. Inténtalo en un rato."


class InvalidIvrDigits(DomainError):
    message = "Solo números, *, # y w (pausa), máximo 32."


# ---------- pedidos ----------


class OrderNotFound(DomainError):
    status_code = 404
    message = "Pedido no encontrado."


class EmptyOrder(DomainError):
    message = "¿Qué pido? Falta al menos un producto."


class InvalidOrderMode(DomainError):
    message = "Modo no válido."


class MissingAddress(DomainError):
    message = "Falta tu dirección de entrega. Añádela en Ajustes."


class InvalidMaxPrice(DomainError):
    message = "El precio máximo debe ser mayor que cero."


class CallInProgress(DomainError):
    status_code = 409
    message = "Ya tienes una llamada en curso."


class DailyLimitReached(DomainError):
    status_code = 429
    message = "Has llegado al límite de llamadas de hoy."


class CallNotPlaced(DomainError):
    status_code = 502
    message = "No he podido llamar. Inténtalo en un rato."


class MissingCustomerPhone(DomainError):
    message = "Para pasarte la llamada necesito tu teléfono. Añádelo en Perfil."


class CallNotActive(DomainError):
    status_code = 409
    message = "Esta llamada ya ha terminado."


class NotWaitingForAnswer(DomainError):
    status_code = 409
    message = "Laia no está esperando respuesta."


class EmptyAnswer(DomainError):
    message = "Escribe una respuesta."


class CommandNotUnderstood(DomainError):
    status_code = 422
    message = "No he entendido qué quieres pedir."


# ---------- servicios externos ----------


class LanguageModelUnavailable(DomainError):
    status_code = 502
    message = "No he podido entender la orden. Inténtalo otra vez."


class TelegramNotConfigured(DomainError):
    status_code = 503
    message = "Telegram no está configurado en el servidor."


class MessageNotSent(Exception):
    """Telegram no responde. No llega a la API: Laia sigue con la llamada igualmente."""
