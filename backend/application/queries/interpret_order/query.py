from domain.exceptions import BusinessNotFound, CommandNotUnderstood


class InterpretOrderQuery:
    """Gemma lee la orden ("pide una pizza en Tres Hermanas...") y devuelve un borrador. No guarda nada.

    Devuelve (pedido entendido, negocio o None). Si no hay negocio, parsed.business_name dice cuál buscar.
    """

    def __init__(self, repositories, language_model_service):
        self.repositories = repositories
        self.language_model_service = language_model_service

    def execute(self, dto):
        business = None
        if dto.business_id:
            business = self.repositories.businesses.find(dto.business_id)
            if not business:
                raise BusinessNotFound()
            business.ensure_callable()
        if len((dto.command or "").strip()) < 3:
            raise CommandNotUnderstood("Dime qué quieres pedir.")
        parsed = self.language_model_service.parse_command(dto.command)
        if not parsed.items:
            raise CommandNotUnderstood()
        if business is None and not parsed.business_name:
            raise CommandNotUnderstood("¿A qué sitio llamo? Dime el nombre, por ejemplo «en Tres Hermanas».")
        return parsed, business
