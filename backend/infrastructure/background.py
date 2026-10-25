"""Trabajo en segundo plano de las llamadas en curso (guardar cambios, avisar por Telegram).

Un único hilo: los cambios de una llamada se guardan en orden y no bloquean la voz.
"""

from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="laia-bg")


def run_in_background(fn):
    def job():
        close_old_connections()
        try:
            fn()
        finally:
            close_old_connections()

    return _executor.submit(job)
