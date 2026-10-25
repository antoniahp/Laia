"""Entrada del audio de las llamadas. Twilio abre este WebSocket cuando el negocio contesta."""

import logging

from asgiref.sync import sync_to_async
from pipecat.runner.utils import parse_telephony_websocket

from application.queries.authorize_voice_stream.query import AuthorizeVoiceStreamQuery
from application.queries.authorize_voice_stream.query_dto import AuthorizeVoiceStreamQueryDTO
from domain.entities import Order
from infrastructure import dependencies
from infrastructure.voice.pipecat_agent import run_voice_agent

logger = logging.getLogger(__name__)


def _authorize(order_id, secret):
    query = AuthorizeVoiceStreamQuery(dependencies.get_repositories(), dependencies.get_live_calls())
    return query.execute(AuthorizeVoiceStreamQueryDTO(order_id=order_id, secret=secret))


async def voice_websocket(websocket):
    await websocket.accept()
    transport_type, call_data = await parse_telephony_websocket(websocket)
    params = call_data.body or {}
    call = None
    if transport_type == "twilio":
        call = await sync_to_async(_authorize)(params.get("order_id", ""), params.get("secret", ""))
    if call is None:
        logger.warning("Audio rechazado: pedido o secreto no válidos")
        await websocket.close()
        return

    logger.info("Llamada conectada: pedido %s", call.order.id)
    try:
        await run_voice_agent(websocket, call_data.stream_id, call_data.call_id, call)
    except Exception:
        logger.exception("Laia no pudo atender la llamada")
        if not call.order.is_finished:
            call.log("Laia tuvo un problema técnico y colgó.")
            call.set_status(Order.FAILED)
        await sync_to_async(call.flush)()
    finally:
        dependencies.get_live_calls().remove(call.order.id)
