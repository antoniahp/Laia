"""Los errores para la app en inglés (la app manda Accept-Language: en)."""

EN = {
    "No se ha podido completar la operación.": "Something went wrong.",
    "Ese email no es válido.": "That email is not valid.",
    "La contraseña debe tener al menos 8 caracteres.": "The password must be at least 8 characters.",
    "Código de invitación incorrecto.": "Wrong invite code.",
    "Ya existe una cuenta con ese email.": "There is already an account with that email.",
    "Email o contraseña incorrectos.": "Wrong email or password.",
    "Sesión caducada. Vuelve a entrar.": "Session expired. Please log in again.",
    "Para usar Laia tienes que aceptar las condiciones y la política de privacidad.": "To use Laia you need to accept the terms and the privacy policy.",
    "Tienes una llamada en curso. Espera a que termine para borrar tu cuenta.": "You have a call in progress. Wait until it ends to delete your account.",
    "Solo para administradores.": "Admins only.",
    "No entiendo ese teléfono. Escríbelo con prefijo, por ejemplo +34 600 111 222.": "I don't understand that phone. Write it with the country code, e.g. +34 600 111 222.",
    "Ese teléfono no es válido.": "That phone number is not valid.",
    "Laia todavía no llama a ese país.": "Laia doesn't call that country yet.",
    "Laia no llama a números de tarificación especial o de servicios.": "Laia doesn't call premium-rate or service numbers.",
    "Revisa el nombre y el idioma del negocio.": "Check the business name and language.",
    "Negocio no encontrado.": "Business not found.",
    "Ese número no está permitido.": "That number is not allowed.",
    "Laia solo llama a negocios verificados. Este aún está pendiente.": "Laia only calls verified businesses. This one is still pending.",
    "Estado no válido.": "Invalid status.",
    "No encuentro ese negocio. Prueba con el nombre y la ciudad, o propónlo a mano.": "I can't find that business. Try the name and city, or suggest it manually.",
    "No encuentro ese negocio en tu lista. Para buscar en Google Maps hay que configurar GOOGLE_PLACES_API_KEY.": "That business isn't in your list, and Google Maps search isn't configured.",
    "Google Maps no me da el teléfono de ese negocio ahora mismo. Inténtalo en un rato.": "Google Maps isn't giving me that business's phone right now. Try again later.",
    "Dime el nombre del sitio.": "Tell me the name of the place.",
    "Solo números, *, # y w (pausa), máximo 32.": "Only digits, *, # and w (pause), 32 max.",
    "Pedido no encontrado.": "Order not found.",
    "¿Qué pido? Falta al menos un producto.": "What should I order? Add at least one item.",
    "Modo no válido.": "Invalid mode.",
    "Falta tu dirección de entrega. Añádela en Ajustes.": "Your delivery address is missing. Add it in Profile.",
    "El precio máximo debe ser mayor que cero.": "The max price must be greater than zero.",
    "Ya tienes una llamada en curso.": "You already have a call in progress.",
    "Has llegado al límite de llamadas de hoy.": "You've reached today's call limit.",
    "No he podido llamar. Inténtalo en un rato.": "I couldn't place the call. Try again later.",
    "No he podido pasarte la llamada. Inténtalo otra vez.": "I couldn't pass you the call. Try again.",
    "Para pasarte la llamada necesito tu teléfono. Añádelo en Perfil.": "To pass you the call I need your phone. Add it in Profile.",
    "Esta llamada ya ha terminado.": "This call has already ended.",
    "Laia no está esperando respuesta.": "Laia isn't waiting for an answer.",
    "Escribe una respuesta.": "Write an answer.",
    "No he entendido qué quieres pedir.": "I didn't understand what you want to order.",
    "Dime qué quieres pedir.": "Tell me what you want to order.",
    "¿A qué sitio llamo? Dime el nombre, por ejemplo «en Tres Hermanas».": 'Which place should I call? Tell me the name, e.g. "from Tres Hermanas".',
    "No he podido entender la orden. Inténtalo otra vez.": "I couldn't understand that. Try again.",
    "Telegram no está configurado en el servidor.": "Telegram isn't configured on the server.",
    "El bot de Telegram no responde ahora mismo.": "The Telegram bot isn't answering right now.",
    "Inicia sesión.": "Please log in.",
}


def in_language(request, message):
    """El mensaje en inglés si la app está en inglés; si no, tal cual."""
    if not request.headers.get("Accept-Language", "").lower().startswith("en"):
        return message
    if message.startswith("Laia todavía no llama a ese país"):
        return "Laia doesn't call that country yet."
    return EN.get(message, message)
