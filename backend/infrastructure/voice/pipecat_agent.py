"""El agente de voz: Laia hablando por teléfono con el negocio.

Tubería (Pipecat):
  Twilio (audio) -> Whisper u ElevenLabs Scribe (oído) -> Gemma vía Ollama (cerebro, open-weight)
                 -> ElevenLabs (voz) -> Twilio

Las decisiones de dinero (precio máximo, alternativas) las toman las reglas del dominio
(Order.accepts_price, Order.next_alternative), no el modelo de IA.
"""

import asyncio
import logging

from django.conf import settings
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndWorkerFrame, FunctionCallResultProperties, LLMMessagesAppendFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair, LLMUserAggregatorParams
from pipecat.processors.frame_processor import FrameDirection
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams, FastAPIWebsocketTransport
from pipecat.turns.user_mute.mute_until_first_bot_complete_user_mute_strategy import (
    MuteUntilFirstBotCompleteUserMuteStrategy,
)
from pipecat.turns.user_start.transcription_user_turn_start_strategy import TranscriptionUserTurnStartStrategy
from pipecat.turns.user_start.vad_user_turn_start_strategy import VADUserTurnStartStrategy
from pipecat.turns.user_stop.speech_timeout_user_turn_stop_strategy import SpeechTimeoutUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.workers.runner import WorkerRunner

from domain.entities import Order
from domain.rules.answers import is_no, is_yes
from domain.rules.languages import LANGUAGES, language_name

logger = logging.getLogger(__name__)

HOLD_PHRASES = {
    "es": "Un momento, por favor, lo consulto enseguida.",
    "en": "One moment please, let me check that quickly.",
    "de": "Einen Moment bitte, ich frage kurz nach.",
    "fr": "Un instant s'il vous plaît, je vérifie tout de suite.",
    "it": "Un attimo per favore, controllo subito.",
    "pt": "Um momento, por favor, vou confirmar já.",
    "ja": "少々お待ちください。すぐに確認します。",
}


DIGITS = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]


def spoken_phone(phone):
    """«600111222» → «seis cero cero, uno uno uno, dos dos dos»: dictado despacio, como una persona."""
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if digits.startswith("34") and len(digits) == 11:
        digits = digits[2:]
    groups = [digits[i : i + 3] for i in range(0, len(digits), 3)]
    return ", ".join(" ".join(DIGITS[int(d)] for d in g) for g in groups)


def system_prompt(call):
    order, customer = call.order, call.customer
    alternatives = ", ".join(order.alternatives) if order.alternatives else "ninguna"
    price = f"{order.max_price:.2f} EUR en total" if order.max_price else "sin límite"
    task = {
        Order.ORDER: "Hacer un pedido para entrega a domicilio. El pago lo hace tu usuario en la entrega "
        "o mediante un enlace que le envíe el negocio. Nunca des datos de tarjeta.",
        Order.BOOKING: "Hacer una reserva (mesa, cita o habitación) a nombre de tu usuario, con su teléfono de contacto. "
        "Si piden una tarjeta como garantía, NO la des: llama a ask_user. Cuando la confirmen, llama a "
        "order_confirmed con total_price 0 si no hay precio.",
    }.get(order.mode, "Solo hacer una consulta (precio, disponibilidad, horario, envío). NO compres ni reserves nada.")
    address = customer.address if order.mode == Order.ORDER else "no hace falta"
    first = order.items[0] if order.items else ""
    opening = {
        Order.ORDER: f"Hola, buenas. Soy la IA y quería encargar {first}.",
        Order.BOOKING: f"Hola, buenas. Soy la IA y quería hacer una reserva: {first}.",
    }.get(order.mode, f"Hola, buenas. Soy la IA y quería preguntar una cosa: {first}.")
    return f"""Eres Laia, una asistente que hace llamadas telefónicas por su usuario.
Estás en una llamada de teléfono REAL con el negocio "{order.business_name}".

IDIOMA: empieza en {language_name(order.language)}. Si el negocio te contesta o te habla en otro idioma
(por ejemplo inglés), cambia a ese idioma y sigue en él toda la llamada. Los textos que mandas a las
herramientas con sufijo _es escríbelos en español, porque los lee tu usuario.

TU MISIÓN: {task}
- Lo que quiere el usuario: {", ".join(order.items)}
- Alternativas si no hay: {alternatives}
- Precio máximo: {price}
- Notas: {order.notes or "ninguna"}
- Nombre para el pedido: {customer.name or "no indicado"}
- Dirección de entrega: {address or "no indicada"}
- Teléfono de contacto: {spoken_phone(customer.phone) or "no indicado"} (díctalo exactamente así, despacio, por grupos)

CÓMO HABLAR (tiene que sonar como una persona normal llamando por teléfono):
- Al empezar, saluda y di directamente lo que quieres, en UNA frase corta y natural, incluyendo que eres
  la IA (obligatorio por ley, no lo omitas). Ejemplo: "{opening}"
  Dilo en el idioma del negocio. No digas el nombre del cliente ni más datos al presentarte.
- Da SOLO el dato que te piden, uno cada vez: si piden la dirección, di solo la dirección; el nombre y el
  teléfono únicamente si te los piden después. Si al final no te han pedido la dirección, ofrécela con
  una pregunta corta ("¿Os doy la dirección?"). Si te preguntan si es para recoger o a domicilio, di que a domicilio.
- Si te preguntan si eres una persona o una máquina, di siempre la verdad: eres una IA.
- En español, coloquial de España (y en otro idioma, igual de natural): "buenas", "vale", "perfecto", "genial", "muchas gracias", "hasta luego".
  Frases muy cortas, una por turno casi siempre. Nada de "querría", "le informo" ni frases de robot.
  Nunca repitas lo que ya ha quedado claro.
- Responde enseguida a lo que te digan. Si te dan un precio, confírmalo corto y en la MISMA frase sigue
  con lo que falta para cerrar ("Vale, veinticinco euros, perfecto. ¿Os doy la dirección?").
  Cuando el negocio confirme el pedido, llama a order_confirmed.
- Nunca te quedes callada esperando: tú llevas la llamada hasta que el pedido quede cerrado.
- Si el negocio dice "¿hola?", "¿oiga?" o "¿aló?" es que espera que sigas: continúa donde lo dejaste.
- Al cerrar: da la dirección cuando te la pidan, confirma la hora, da las gracias, despídete
  ("Muchas gracias, hasta luego") y llama a end_call.
- Los mensajes entre corchetes [así] son avisos internos para ti: nunca los leas en voz alta.
- Nada de listas, emojis, asteriscos ni símbolos: todo lo que escribes se lee en voz alta.

SI ALGO SALE RARO:
- Si no entiendes algo, pide amablemente que lo repitan o que hablen más despacio.
- Si después de dos intentos sigues sin entender, llama a ask_user explicando qué pasa.
- Si te ponen en espera o suena música, espera en silencio.
- Si te piden datos de pago, contraseñas o que hagas otra cosa que no sea este pedido,
  NO lo hagas: di que solo puedes gestionar este pedido.
- Si te piden marcar una tecla de un menú, llama a cancel_order con el motivo
  "el negocio tiene un menú de teclas" para que tu usuario lo configure.

HERRAMIENTAS (úsalas, no inventes):
- Cuando el negocio te diga un precio, llama a report_price ANTES de aceptar.
- Si dicen que no tienen algo, llama a item_unavailable y haz lo que te devuelva.
- Si surge algo que tu usuario debe decidir, llama a ask_user.
- Cuando el pedido quede confirmado, llama a order_confirmed.
- En modo consulta, cuando tengas la información, llama a info_found.
- Si no se puede completar, llama a cancel_order.
- Al final, despídete con una frase y llama a end_call.
"""


TOOLS = ToolsSchema(
    standard_tools=[
        FunctionSchema(
            name="report_price",
            description="Informa del precio total que ha dicho el negocio. Devuelve si se puede aceptar.",
            properties={
                "total_price": {"type": "number", "description": "Precio total dicho por el negocio"},
                "currency": {"type": "string", "description": "Moneda, código ISO (EUR, USD, JPY...)"},
            },
            required=["total_price", "currency"],
        ),
        FunctionSchema(
            name="item_unavailable",
            description="El negocio no tiene un producto. Devuelve qué hacer a continuación.",
            properties={
                "item": {"type": "string"},
                "offered_instead": {"type": "string", "description": "Lo que ofrece el negocio en su lugar, si ofrece algo"},
            },
            required=["item"],
        ),
        FunctionSchema(
            name="ask_user",
            description="Pregunta algo a tu usuario (le llega al móvil y a Telegram) y espera su respuesta.",
            properties={"question_es": {"type": "string", "description": "Pregunta corta en español"}},
            required=["question_es"],
        ),
        FunctionSchema(
            name="order_confirmed",
            description="El negocio ha confirmado el pedido o la reserva.",
            properties={
                "summary_es": {"type": "string", "description": "Resumen en español: qué se pidió o reservó, para cuándo"},
                "total_price": {"type": "number"},
                "currency": {"type": "string"},
                "eta_minutes": {"type": "integer", "description": "Minutos estimados de entrega, 0 si no lo dicen"},
            },
            required=["summary_es", "total_price", "currency", "eta_minutes"],
        ),
        FunctionSchema(
            name="info_found",
            description="Modo consulta: ya tienes la información pedida.",
            properties={"summary_es": {"type": "string", "description": "Lo que has averiguado, en español"}},
            required=["summary_es"],
        ),
        FunctionSchema(
            name="cancel_order",
            description="No se puede completar el pedido.",
            properties={"reason_es": {"type": "string", "description": "Motivo en español"}},
            required=["reason_es"],
        ),
        FunctionSchema(name="end_call", description="Cuelga. Llámala justo después de despedirte.", properties={}, required=[]),
    ]
)


def register_tools(llm, call):
    order = call.order

    async def hold(params):
        await params.llm.push_frame(TTSSpeakFrame(HOLD_PHRASES.get(order.language, HOLD_PHRASES["en"])))

    async def report_price(params):
        price = float(params.arguments.get("total_price", 0))
        currency = str(params.arguments.get("currency", "EUR")).upper()
        call.log(f"El negocio dice que cuesta {price:g} {currency}.")
        if order.max_price is None:
            return await params.result_callback({"accept": True})
        if currency != "EUR":
            # No convertimos monedas a ojo: decide el usuario
            await hold(params)
            answer = await call.ask_user(f"Cuesta {price:g} {currency}. Tu máximo era {order.max_price:g} €. ¿Lo pido?")
            return await params.result_callback({"accept": is_yes(answer), "user_answer": answer})
        if order.accepts_price(price):
            return await params.result_callback({"accept": True})
        call.log(f"Supera tu máximo de {order.max_price:g} €. No se acepta.")
        await params.result_callback(
            {
                "accept": False,
                "instruction": "Es demasiado caro. Pregunta si hay algo similar más barato dentro del máximo; "
                "si no, discúlpate amablemente, llama a cancel_order y despídete.",
            }
        )

    async def item_unavailable(params):
        item = params.arguments.get("item", "")
        offered = params.arguments.get("offered_instead") or ""
        call.log(f"No tienen: {item}." + (f" Ofrecen: {offered}." if offered else ""))
        if order.must_ask_before_alternative():
            await hold(params)
            question = (
                f"No tienen {item}. Ofrecen {offered}. ¿Lo pido?" if offered else f"No tienen {item}. ¿Qué pido en su lugar? (o di 'nada')"
            )
            answer = await call.ask_user(question)
            if is_no(answer):
                instruction = "El usuario no quiere otra cosa. Llama a cancel_order y despídete amablemente."
            elif is_yes(answer) and offered:
                instruction = f"El usuario acepta: {offered}. Pídelo."
            else:
                instruction = f"El usuario quiere en su lugar: {answer}. Pídelo."
            return await params.result_callback({"instruction": instruction})
        alternative = order.next_alternative()
        if alternative:
            call.log(f"Laia pide la alternativa: {alternative}.")
            return await params.result_callback({"instruction": f"Pide esta alternativa: {alternative}."})
        await params.result_callback({"instruction": "No quedan alternativas. Llama a cancel_order y despídete amablemente."})

    async def ask_user(params):
        await hold(params)
        answer = await call.ask_user(params.arguments.get("question_es", "¿Qué hago?"))
        if answer is None:
            return await params.result_callback(
                {"user_answer": None, "instruction": "El usuario no responde. Elige la opción más prudente."}
            )
        await params.result_callback({"user_answer": answer})

    async def order_confirmed(params):
        a = params.arguments
        order.confirm(a.get("summary_es", ""), a.get("total_price"), a.get("currency", "EUR"), a.get("eta_minutes", 0))
        call.set_status(Order.DONE)
        await params.result_callback({"ok": True, "instruction": "Agradece y despídete, luego llama a end_call."})

    async def info_found(params):
        order.report_info(params.arguments.get("summary_es", ""))
        call.set_status(Order.DONE)
        await params.result_callback({"ok": True, "instruction": "Agradece y despídete, luego llama a end_call."})

    async def cancel_order(params):
        order.cancel(params.arguments.get("reason_es", ""))
        call.set_status(Order.CANCELLED)
        await params.result_callback({"ok": True, "instruction": "Despídete amablemente y llama a end_call."})

    async def end_call(params):
        call.log("Laia ha colgado.")
        await params.result_callback({"ok": True}, properties=FunctionCallResultProperties(run_llm=False))
        await params.llm.push_frame(EndWorkerFrame(), FrameDirection.UPSTREAM)

    # Las herramientas que esperan al usuario no se cancelan si el negocio habla mientras tanto
    waiting = {"cancel_on_interruption": False, "timeout_secs": 120}
    llm.register_function("report_price", report_price, **waiting)
    llm.register_function("item_unavailable", item_unavailable, **waiting)
    llm.register_function("ask_user", ask_user, **waiting)
    llm.register_function("order_confirmed", order_confirmed)
    llm.register_function("info_found", info_found)
    llm.register_function("cancel_order", cancel_order)
    llm.register_function("end_call", end_call)


def _keyterms(call):
    """Palabras que seguramente saldrán en la llamada: ayudan mucho a entenderlas."""
    order = call.order
    terms = []
    for text in [order.business_name, *order.items, *order.alternatives, "euros", "a domicilio"]:
        # ElevenLabs solo acepta términos de hasta 20 letras: los largos van palabra a palabra
        for term in [text] if len(text or "") <= 20 else text.split():
            if term and len(term) <= 20 and term not in terms:
                terms.append(term)
    return terms[:20]


def _elevenlabs_stt(call, language):
    from pipecat.services.elevenlabs.stt import CommitStrategy, ElevenLabsRealtimeSTTService

    # ElevenLabs decide sola cuándo acaba cada frase: así el texto llega siempre, sin depender de nuestro VAD
    return ElevenLabsRealtimeSTTService(
        api_key=settings.LAIA["ELEVENLABS_API_KEY"],
        commit_strategy=CommitStrategy.VAD,
        settings=ElevenLabsRealtimeSTTService.Settings(language=language, keyterms=_keyterms(call), vad_silence_threshold_secs=0.4),
    )


def build_stt(call, language):
    """El oído de Laia. ElevenLabs Scribe entiende mejor el audio de teléfono; Whisper es la opción abierta y local."""
    cfg = settings.LAIA
    if cfg["STT_PROVIDER"] == "elevenlabs":
        return _elevenlabs_stt(call, language)
    try:
        from pipecat.services.whisper.stt import WhisperSTTService
    except ImportError as error:
        # Mejor oír con ElevenLabs que colgar al negocio
        logger.error("Whisper no está disponible (%s): uso ElevenLabs para entender la llamada", error)
        return _elevenlabs_stt(call, language)

    return WhisperSTTService(
        device=cfg["WHISPER_DEVICE"],
        settings=WhisperSTTService.Settings(
            model=cfg["WHISPER_MODEL"],
            language=language,
            hotwords=" ".join(_keyterms(call)),
            # Audio de teléfono: Whisper suele creer que es «ruido». Mejor transcribir de más que de menos.
            no_speech_prob=0.9,
            initial_prompt="Llamada telefónica a un restaurante: hola, dígame, ¿qué desea?, son 12 euros, ¿a qué dirección?",
        ),
    )


async def run_voice_agent(websocket, stream_id, call_id, call):
    cfg = settings.LAIA
    order = call.order
    language = Language(order.language) if order.language in LANGUAGES else Language.ES

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            serializer=TwilioFrameSerializer(
                stream_sid=stream_id,
                call_sid=call_id,
                account_sid=cfg["TWILIO_ACCOUNT_SID"],
                auth_token=cfg["TWILIO_AUTH_TOKEN"],
            ),
        ),
    )
    llm = OLLamaLLMService(
        base_url=f"{cfg['OLLAMA_HOST']}/v1",
        api_key=cfg["OLLAMA_API_KEY"] or "ollama",
        settings=OLLamaLLMService.Settings(model=cfg["OLLAMA_MODEL"], temperature=0.4),
    )
    tts = ElevenLabsTTSService(
        api_key=cfg["ELEVENLABS_API_KEY"],
        settings=ElevenLabsTTSService.Settings(
            voice=cfg["ELEVENLABS_VOICE_ID"],
            model=cfg["ELEVENLABS_MODEL"],
            # Sin idioma fijo: la voz pronuncia en el idioma del texto, así Laia puede cambiar de idioma
            # si el negocio contesta en otro (p. ej. inglés en Mallorca)
            language=None,
            # Algo menos de estabilidad = entonación más humana; sin pasarse para que no suene rara
            stability=0.35,
            similarity_boost=0.8,
            style=0.0,
            use_speaker_boost=True,
        ),
    )
    register_tools(llm, call)

    context = LLMContext(messages=[{"role": "system", "content": system_prompt(call)}], tools=TOOLS)
    # Turnos de conversación rápidos y robustos para audio de teléfono:
    # - mientras Laia se presenta no se la interrumpe (el "clic" al descolgar la cortaba)
    # - el turno del negocio termina 0,6 s después de su última palabra, aunque el VAD no lo detecte
    aggregators = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(params=VADParams(confidence=0.6, min_volume=0.3)),
            user_turn_strategies=UserTurnStrategies(
                start=[VADUserTurnStartStrategy(), TranscriptionUserTurnStartStrategy()],
                stop=[SpeechTimeoutUserTurnStopStrategy(user_speech_timeout=0.6)],
            ),
            user_mute_strategies=[MuteUntilFirstBotCompleteUserMuteStrategy()],
            user_turn_stop_timeout=2.0,
            empty_user_turn=None,
        ),
    )
    pipeline = Pipeline(
        [transport.input(), build_stt(call, language), aggregators.user(), llm, tts, transport.output(), aggregators.assistant()]
    )
    # 16 kHz dentro de Laia: Whisper y ElevenLabs trabajan a 16 kHz; el serializador de Twilio convierte
    # desde/hacia los 8 kHz del teléfono. Música de espera o silencios largos: no colgar demasiado pronto.
    worker = PipelineWorker(pipeline, params=PipelineParams(audio_in_sample_rate=16000, audio_out_sample_rate=16000), idle_timeout_secs=150)

    business_spoke = asyncio.Event()
    laia_spoke = False

    async def nudge(text):
        """Le dice a Laia qué ha pasado (sin que lo oiga el negocio) y la hace hablar."""
        await worker.queue_frames([LLMMessagesAppendFrame([{"role": "user", "content": text}], run_llm=True)])

    @aggregators.user().event_handler("on_user_turn_started")
    async def on_business_starts(_aggregator, _strategy):
        business_spoke.set()

    @aggregators.user().event_handler("on_user_turn_stopped")
    async def on_business_said(_aggregator, _strategy, message):
        text = (message.content or "").strip()
        if text:
            call.add_line("negocio", text)
            return
        # No se ha entendido lo que dijeron
        if not laia_spoke:
            await nudge("[El negocio ha descolgado y ha saludado. Preséntate y di lo que quieres.]")
        else:
            await nudge("[No se ha entendido bien lo que ha dicho el negocio. Pide con naturalidad que lo repita.]")

    @aggregators.assistant().event_handler("on_assistant_turn_stopped")
    async def on_laia_said(_aggregator, message):
        nonlocal laia_spoke
        if (message.content or "").strip():
            laia_spoke = True
        call.add_line("laia", message.content)

    @transport.event_handler("on_client_connected")
    async def on_connected(_transport, _client):
        call.set_status(Order.IN_CALL)
        call.log(f"{order.business_name} ha contestado.")

        # Normalmente el negocio contesta primero ("¿Dígame?"). Si en 2 s no dice nada, empieza Laia.
        async def kickoff():
            try:
                await asyncio.wait_for(business_spoke.wait(), 2)
            except TimeoutError:
                await nudge("[El negocio ha descolgado pero no dice nada. Preséntate y di lo que quieres.]")

        asyncio.create_task(kickoff())

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(_transport, _client):
        if not order.is_finished:
            call.log("La llamada terminó sin cerrar el pedido.")
            call.set_status(Order.FAILED)
        await worker.cancel()

    try:
        await WorkerRunner(handle_sigint=False).run(worker)
    except Exception as error:  # noqa: BLE001
        logger.exception("Error en la llamada")
        call.log(f"Error en la llamada: {error}")
        call.set_status(Order.FAILED)
    finally:
        if not order.is_finished:
            call.set_status(Order.FAILED)
        await asyncio.to_thread(call.flush)
