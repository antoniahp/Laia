"""Escuchar la llamada en directo.

Twilio manda una copia del audio de la llamada (lo que dice el negocio y lo que dice Laia).
`LiveAudioHub` lo mezcla en una sola pista y lo reparte a la app de la persona que escucha.
Todo ocurre en el bucle de eventos del servidor; el audio no se guarda nunca.
"""

import asyncio

from domain.rules.audio import mix_frames, mulaw_to_pcm16

FRAME_MS = 20
FLUSH_DELAY_MS = 80  # esperamos un poco a la otra pista antes de mezclar


class ListenChannel:
    """El audio de una llamada: mezcla las dos pistas y lo reparte a quien escucha."""

    def __init__(self):
        self.listeners = set()
        self._slots = {}  # instante (ms) -> {pista: pcm}
        self._latest = 0
        self.has_audio = False

    def add_media(self, track, timestamp_ms, mulaw):
        self.has_audio = True
        slot = int(timestamp_ms) // FRAME_MS * FRAME_MS
        self._slots.setdefault(slot, {})[track] = mulaw_to_pcm16(mulaw)
        self._latest = max(self._latest, slot)
        self._flush(older_than=self._latest - FLUSH_DELAY_MS)

    def _flush(self, older_than):
        ready = sorted(s for s in self._slots if s <= older_than)
        if not ready:
            return
        chunk = b"".join(mix_frames(list(self._slots.pop(s).values())) for s in ready)
        for queue in list(self.listeners):
            if queue.qsize() < 100:  # si la app va lenta, mejor perder audio que acumular retraso
                queue.put_nowait(chunk)

    def close(self):
        self._flush(older_than=self._latest)
        for queue in list(self.listeners):
            queue.put_nowait(None)


class LiveAudioHub:
    def __init__(self):
        self._channels = {}

    def channel(self, order_id):
        return self._channels.setdefault(str(order_id), ListenChannel())

    def subscribe(self, order_id):
        queue = asyncio.Queue()
        self.channel(order_id).listeners.add(queue)
        return queue

    def unsubscribe(self, order_id, queue):
        channel = self._channels.get(str(order_id))
        if channel:
            channel.listeners.discard(queue)

    def drop_if_unused(self, order_id):
        """Si nadie escucha y Twilio no ha mandado audio, el canal sobra."""
        channel = self._channels.get(str(order_id))
        if channel and not channel.listeners and not channel.has_audio:
            self._channels.pop(str(order_id), None)

    def close(self, order_id):
        channel = self._channels.pop(str(order_id), None)
        if channel:
            channel.close()


live_audio = LiveAudioHub()
