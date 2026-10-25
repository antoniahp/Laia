"""Llamadas en curso.

`LiveCall` envuelve el pedido mientras dura la llamada. Lo usan a la vez:
- el agente de voz (asíncrono, en el bucle de eventos del WebSocket),
- la API y los webhooks (síncronos, en los hilos de Django).

Por eso es seguro entre hilos: guarda los cambios en segundo plano (`run_in_background`)
y las respuestas del usuario llegan a la llamada con `call_soon_threadsafe`.

Las llamadas en curso viven en la memoria de un único proceso del servidor.
"""

import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from domain.entities import Order
from domain.exceptions import LanguageModelUnavailable, MessageNotSent

logger = logging.getLogger(__name__)

# Las traducciones van aparte: si el modelo tarda, no retrasan el guardado de la llamada
_translations = ThreadPoolExecutor(max_workers=2, thread_name_prefix="laia-tr")

# Campos que cambian durante la llamada
LIVE_FIELDS = ["status", "call_sid", "transcript", "events", "pending_question", "result", "alternatives_tried"]


@dataclass(frozen=True)
class Customer:
    name: str
    address: str
    phone: str


def run_now(fn):
    """Ejecutor para tests: hace el trabajo al momento, en el mismo hilo."""
    fn()
    return None


class LiveCall:
    def __init__(
        self,
        order,
        customer,
        telegram_chat_id,
        repositories,
        message_service,
        run_in_background=run_now,
        translator=None,
    ):
        self.order = order
        self.customer = customer
        self.telegram_chat_id = telegram_chat_id
        self._repositories = repositories
        self._messages = message_service
        self._run = run_in_background
        self._translator = translator  # traduce al español si el negocio habla otro idioma
        self._lock = threading.RLock()
        self._loop = None
        self._answers = None
        self._last_save = None

    # ---------- guardar ----------

    def _persist(self):
        self._last_save = self._run(lambda: self._repositories.orders.save(self.order, LIVE_FIELDS))

    def flush(self):
        """Espera a que todo esté guardado. Síncrono: desde código asíncrono, usa asyncio.to_thread."""
        future = self._run(lambda: self._repositories.orders.save(self.order, LIVE_FIELDS))
        if future is not None:
            future.result()

    # ---------- lo que pasa en la llamada ----------

    def log(self, text):
        with self._lock:
            self.order.log(text)
        self._persist()

    def add_line(self, speaker, text):
        with self._lock:
            before = len(self.order.transcript)
            self.order.add_line(speaker, text)
            index = before if len(self.order.transcript) > before else None
        self._persist()
        if index is not None and self._translator and self.order.language != "es":
            if self._run is run_now:
                self._translate_line(index)
            else:
                _translations.submit(self._translate_line, index)

    def _translate_line(self, index):
        """Traduce al español lo que se dice en otro idioma, para que lo sigas en la app."""
        line = self.order.transcript[index]
        try:
            translated = self._translator.translate(line["text"], self.order.language, "es")
        except LanguageModelUnavailable:
            return
        except Exception:
            logger.exception("No se pudo traducir una frase")
            return
        if not translated:
            return
        with self._lock:
            transcript = list(self.order.transcript)
            transcript[index] = {**transcript[index], "tr": translated.strip()}
            self.order.transcript = transcript
        self._persist()

    def set_call_id(self, call_id):
        with self._lock:
            self.order.call_sid = call_id
        self._persist()

    def set_status(self, status):
        with self._lock:
            changed = self.order.mark(status)
        self._persist()
        if changed and status in Order.FINAL_STATUSES:
            self._run(self._notify_result)

    def _send(self, text, buttons=None):
        if not self.telegram_chat_id:
            return
        try:
            self._messages.send(self.telegram_chat_id, text, buttons)
        except MessageNotSent:
            pass  # Telegram caído: la llamada sigue

    def _notify_result(self):
        o = self.order
        summary = (o.result or {}).get("summary", "")
        if o.status == Order.DONE:
            r = o.result or {}
            lines = [f"✅ {o.business_name}: {summary}"]
            if r.get("total_price") is not None:
                lines.append(f"Total: {r['total_price']} {r.get('currency', 'EUR')}")
            if r.get("eta_minutes"):
                lines.append(f"Llega en unos {r['eta_minutes']} min")
            text = "\n".join(lines)
        elif o.status == Order.CANCELLED:
            what = "la reserva" if o.mode == Order.BOOKING else "el pedido"
            text = f"🚫 {o.business_name}: no se hizo {what}. {summary}"
        elif o.status == Order.TRANSFERRED:
            text = f"📞 {o.business_name}: te he pasado la llamada. Contesta en tu móvil."
        else:
            last = o.events[-1] if o.events else ""
            text = f"⚠️ {o.business_name}: la llamada no salió bien. {last}"
        self._send(text.strip())

    # ---------- preguntar al usuario (app + Telegram) ----------

    @property
    def is_waiting_for_user(self):
        return self.order.pending_question is not None

    async def ask_user(self, question, timeout=90):
        self._loop = asyncio.get_running_loop()
        self._answers = asyncio.Queue()
        with self._lock:
            previous = self.order.status
            self.order.pending_question = question
            self.order.mark(Order.WAITING_USER)
        self.log(f"Laia te pregunta: {question}")
        buttons = [[("Sí", f"a|{self.order.id}|Sí"), ("No", f"a|{self.order.id}|No")]]
        self._run(lambda: self._send(f"❓ {self.order.business_name}: {question}\n(o escríbeme otra respuesta)", buttons))
        try:
            return await asyncio.wait_for(self._answers.get(), timeout)
        except TimeoutError:
            self.log("No respondiste a tiempo.")
            return None
        finally:
            with self._lock:
                self.order.pending_question = None
                if self.order.status == Order.WAITING_USER:
                    self.order.mark(previous)
            self._persist()

    def answer(self, text):
        """Se puede llamar desde cualquier hilo. Devuelve False si Laia no esperaba respuesta."""
        with self._lock:
            if not self.is_waiting_for_user or self._loop is None:
                return False
        self.log(f"Respondiste: {text}")
        self._loop.call_soon_threadsafe(self._answers.put_nowait, text)
        return True


class LiveCallRegistry:
    def __init__(self):
        self._calls = {}
        self._lock = threading.Lock()

    def add(self, call):
        with self._lock:
            self._calls[str(call.order.id)] = call

    def get(self, order_id):
        with self._lock:
            return self._calls.get(str(order_id))

    def remove(self, order_id):
        with self._lock:
            self._calls.pop(str(order_id), None)

    def _all(self):
        with self._lock:
            return list(self._calls.values())

    def has_active_call(self, account_id):
        return any(c.order.account_id == account_id and not c.order.is_finished for c in self._all())

    def waiting_for(self, account_id):
        return next((c for c in self._all() if c.order.account_id == account_id and c.is_waiting_for_user), None)

    def for_account(self, account_id):
        return [c for c in self._all() if c.order.account_id == account_id]

    def clear(self):
        with self._lock:
            self._calls.clear()


# Una sola instancia por proceso
live_calls = LiveCallRegistry()
