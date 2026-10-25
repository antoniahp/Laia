from domain.exceptions import SessionExpired


class ExportMyDataQuery:
    """Derecho de acceso y portabilidad: todo lo que Laia guarda de ti, en un JSON."""

    def __init__(self, repositories):
        self.repositories = repositories

    def execute(self, dto):
        account = self.repositories.accounts.find(dto.account_id)
        if not account:
            raise SessionExpired()
        orders = self.repositories.orders.list_for_account(account.id, limit=10_000)
        return {
            "cuenta": {
                "email": account.email,
                "nombre": account.name,
                "direccion": account.address,
                "telefono": account.phone,
                "telegram_conectado": account.has_telegram,
                "condiciones_aceptadas": account.terms_version,
                "condiciones_aceptadas_el": account.terms_accepted_at.isoformat() if account.terms_accepted_at else None,
                "creada_el": account.created_at.isoformat() if account.created_at else None,
            },
            "pedidos": [
                {
                    "negocio": o.business_name,
                    "fecha": o.created_at.isoformat() if o.created_at else None,
                    "estado": o.status,
                    "pedido": o.items,
                    "alternativas": o.alternatives,
                    "precio_maximo": o.max_price,
                    "resultado": o.result,
                    "conversacion": o.transcript,
                }
                for o in orders
            ],
        }
