import hmac


class AuthorizeVoiceStreamQuery:
    """¿Este audio de la compañía telefónica es de una llamada nuestra en curso? Devuelve la LiveCall o None."""

    def __init__(self, repositories, live_calls):
        self.repositories = repositories
        self.live_calls = live_calls

    def execute(self, dto):
        call = self.live_calls.get(dto.order_id)
        if not call or call.order.is_finished:
            return None
        stored = self.repositories.orders.find(call.order.id)
        if not stored or not hmac.compare_digest(dto.secret or "", stored.call_secret):
            return None
        return call
