"""Punto de entrada del servidor (uvicorn core.asgi:application).

- /ws        -> audio de las llamadas (WebSocket de Twilio, agente de voz con Pipecat)
- el resto   -> Django: API Ninja (/api), webhooks (/twilio, /telegram) y admin (/admin)
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django_app = get_asgi_application()

from django.conf import settings  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.routing import Mount, WebSocketRoute  # noqa: E402

from infrastructure.voice.listen_websocket import app_listen_websocket, twilio_listen_websocket  # noqa: E402
from infrastructure.voice.websocket import voice_websocket  # noqa: E402

logger = logging.getLogger("laia")


def _preload_whisper():
    try:
        from faster_whisper.utils import download_model

        download_model(settings.LAIA["WHISPER_MODEL"])
        logger.info("Whisper '%s' listo.", settings.LAIA["WHISPER_MODEL"])
    except Exception as error:  # noqa: BLE001
        logger.warning("No pude descargar Whisper ahora (%s); lo intentaré en la primera llamada.", error)


def _purge_old_conversations():
    from application.commands.purge_old_conversations.command import PurgeOldConversationsCommand
    from application.commands.purge_old_conversations.command_dto import PurgeOldConversationsCommandDTO
    from infrastructure import dependencies

    try:
        count = PurgeOldConversationsCommand(dependencies.get_repositories()).execute(
            PurgeOldConversationsCommandDTO(days=settings.LAIA["RETENTION_DAYS"])
        )
        if count:
            logger.info("Borradas %s conversaciones antiguas.", count)
    except Exception as error:  # noqa: BLE001
        logger.warning("No pude borrar conversaciones antiguas: %s", error)


async def _daily_purge():
    while True:
        await asyncio.get_running_loop().run_in_executor(None, _purge_old_conversations)
        await asyncio.sleep(24 * 3600)


@asynccontextmanager
async def lifespan(_app):
    if settings.LAIA["STT_PROVIDER"] == "whisper":
        asyncio.get_running_loop().run_in_executor(None, _preload_whisper)
    purge = asyncio.create_task(_daily_purge())
    logger.info("Laia lista. Esperando órdenes ✨")
    yield
    purge.cancel()


application = Starlette(
    routes=[
        WebSocketRoute("/ws", voice_websocket),
        WebSocketRoute("/ws/listen", twilio_listen_websocket),
        WebSocketRoute("/ws/app/listen/{order_id}", app_listen_websocket),
        Mount("/", app=django_app),
    ],
    lifespan=lifespan,
)
