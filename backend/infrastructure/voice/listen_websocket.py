"""Escuchar la llamada en directo.

- /ws/listen: Twilio manda aquí una copia del audio (negocio + Laia). Se comprueba el secreto de la llamada.
- /ws/app/listen/{order_id}: la app se conecta con su sesión y recibe el audio mezclado (PCM 16 bits, 8 kHz).
"""

import asyncio
import base64
import json
import logging

from asgiref.sync import sync_to_async
from starlette.websockets import WebSocketDisconnect

from application.queries.authenticate_token.query import AuthenticateTokenQuery
from application.queries.authenticate_token.query_dto import AuthenticateTokenQueryDTO
from application.queries.authorize_voice_stream.query import AuthorizeVoiceStreamQuery
from application.queries.authorize_voice_stream.query_dto import AuthorizeVoiceStreamQueryDTO
from infrastructure import dependencies

logger = logging.getLogger(__name__)
CHECK_EVERY_SECONDS = 5


def _authorize_stream(order_id, secret):
    query = AuthorizeVoiceStreamQuery(dependencies.get_repositories(), dependencies.get_live_calls())
    return query.execute(AuthorizeVoiceStreamQueryDTO(order_id=order_id, secret=secret))


def _owner_of_live_call(token, order_id):
    account = AuthenticateTokenQuery(dependencies.get_repositories(), dependencies.get_token_service()).execute(
        AuthenticateTokenQueryDTO(token=token)
    )
    call = dependencies.get_live_calls().get(order_id)
    return bool(account and call and call.order.account_id == account.id)


async def twilio_listen_websocket(websocket):
    """Copia del audio de Twilio. Mensajes JSON: connected, start, media, stop."""
    await websocket.accept()
    hub = dependencies.get_live_audio()
    order_id = None
    try:
        while True:
            message = json.loads(await websocket.receive_text())
            event = message.get("event")
            if event == "start":
                params = message["start"].get("customParameters", {})
                call = await sync_to_async(_authorize_stream)(params.get("order_id", ""), params.get("secret", ""))
                if call is None:
                    logger.warning("Copia de audio rechazada")
                    await websocket.close()
                    return
                order_id = str(call.order.id)
            elif event == "media" and order_id:
                media = message["media"]
                hub.channel(order_id).add_media(
                    media.get("track", "inbound"), int(media.get("timestamp", 0)), base64.b64decode(media["payload"])
                )
            elif event == "stop":
                break
    except WebSocketDisconnect:
        pass
    finally:
        if order_id:
            hub.close(order_id)


async def app_listen_websocket(websocket):
    """La app escucha: se autentica con su token (cabecera Authorization o ?token=)."""
    order_id = websocket.path_params["order_id"]
    auth = websocket.headers.get("authorization", "")
    token = auth[7:] if auth.lower().startswith("bearer ") else websocket.query_params.get("token", "")
    if not await sync_to_async(_owner_of_live_call)(token, order_id):
        await websocket.close(code=4403)
        return
    await websocket.accept()
    hub = dependencies.get_live_audio()
    queue = hub.subscribe(order_id)
    live_calls = dependencies.get_live_calls()
    try:
        while True:
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=CHECK_EVERY_SECONDS)
            except TimeoutError:
                call = live_calls.get(order_id)
                if call is None or call.order.is_finished:
                    break  # la llamada terminó sin que llegase audio
                continue
            if chunk is None:
                break
            await websocket.send_bytes(chunk)
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(order_id, queue)
        hub.drop_if_unused(order_id)
        try:
            await websocket.close()
        except RuntimeError:
            pass
