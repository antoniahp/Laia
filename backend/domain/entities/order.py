import secrets

from django.db import models

from domain.entities.base_model import BaseModel
from domain.exceptions import EmptyOrder, InvalidMaxPrice, InvalidOrderMode, MissingAddress


def new_call_secret():
    return secrets.token_urlsafe(24)


class Order(BaseModel):
    """Un encargo a Laia: llamar a un negocio para pedir o preguntar algo, con tus reglas."""

    # Estados
    CALLING = "llamando"
    IN_CALL = "en_llamada"
    WAITING_USER = "esperando_tu_respuesta"
    DONE = "pedido_hecho"
    CANCELLED = "cancelado"
    FAILED = "fallido"
    TRANSFERRED = "pasada_a_ti"
    FINAL_STATUSES = (DONE, CANCELLED, FAILED, TRANSFERRED)

    # Modos
    ORDER = "pedido"
    BOOKING = "reserva"
    INQUIRY = "consulta"
    MODES = (ORDER, BOOKING, INQUIRY)

    account = models.ForeignKey("domain.Account", on_delete=models.CASCADE, related_name="orders")
    business = models.ForeignKey("domain.Business", on_delete=models.PROTECT, related_name="orders")
    business_name = models.CharField(max_length=160)
    language = models.CharField(max_length=5)
    mode = models.CharField(max_length=20, default=ORDER)
    items = models.JSONField(default=list)
    alternatives = models.JSONField(default=list, blank=True)
    max_price = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    ask_before_alternative = models.BooleanField(default=False)
    status = models.CharField(max_length=40, default=CALLING, db_index=True)
    call_sid = models.CharField(max_length=64, blank=True)
    call_secret = models.CharField(max_length=64, default=new_call_secret)
    transcript = models.JSONField(default=list, blank=True)
    events = models.JSONField(default=list, blank=True)
    pending_question = models.TextField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    alternatives_tried = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pedido"

    def __str__(self):
        return f"{self.business_name} · {self.status}"

    # ---------- creación ----------

    @classmethod
    def prepare(cls, account, business, mode, items, alternatives, max_price, notes, ask_before_alternative):
        """Comprueba las reglas y devuelve el pedido sin guardar."""
        business.ensure_callable()
        clean_items = [i.strip() for i in items if i and i.strip()]
        if not clean_items:
            raise EmptyOrder()
        if mode not in cls.MODES:
            raise InvalidOrderMode()
        if mode == cls.ORDER and not account.address:
            raise MissingAddress()
        if max_price is not None and max_price <= 0:
            raise InvalidMaxPrice()
        return cls(
            account=account,
            business=business,
            business_name=business.name,
            language=business.language,
            mode=mode,
            items=clean_items,
            alternatives=[a.strip() for a in alternatives if a and a.strip()],
            max_price=max_price,
            notes=(notes or "").strip()[:500],
            ask_before_alternative=ask_before_alternative,
            events=[f"Llamando a {business.name}..."],
        )

    # ---------- estado ----------

    @property
    def is_finished(self):
        return self.status in self.FINAL_STATUSES

    def log(self, text):
        self.events = [*self.events, text]

    def add_line(self, speaker, text):
        if text and text.strip():
            self.transcript = [*self.transcript, {"who": speaker, "text": text.strip()}]

    def mark(self, status):
        """Cambia de estado. Un pedido terminado no vuelve atrás. Devuelve True si cambió."""
        if self.is_finished and status not in self.FINAL_STATUSES:
            return False
        changed = status != self.status
        self.status = status
        return changed

    def confirm(self, summary, total_price=None, currency="EUR", eta_minutes=0):
        self.result = {"summary": summary, "total_price": total_price, "currency": currency, "eta_minutes": eta_minutes}
        self.log(f"{'¡Reserva hecha!' if self.mode == self.BOOKING else '¡Pedido hecho!'} {summary}")

    def report_info(self, summary):
        self.result = {"summary": summary}
        self.log(f"Información: {summary}")

    def transfer_to_customer(self):
        self.result = {"summary": "Te pasé la llamada para que hables tú."}
        self.log("Te he pasado la llamada.")

    def forget_conversation(self):
        """Retención: tras unos días solo se queda el resultado, no la conversación."""
        self.transcript = []
        self.events = []
        self.pending_question = None

    def cancel(self, reason):
        self.result = {"summary": reason}
        self.log(f"No se pudo hacer el pedido: {reason}")

    # ---------- reglas de decisión (en código, no las decide el modelo de IA) ----------

    def accepts_price(self, price):
        return self.max_price is None or price <= self.max_price

    def next_alternative(self):
        if self.alternatives_tried < len(self.alternatives):
            alternative = self.alternatives[self.alternatives_tried]
            self.alternatives_tried += 1
            return alternative
        return None

    def must_ask_before_alternative(self):
        return self.ask_before_alternative or not self.alternatives
