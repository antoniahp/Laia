# Laia · backend

Django + Django Ninja con arquitectura hexagonal y CQRS, la misma organización que alma-estetica.

```
backend/
├── core/                 Proyecto Django: settings, urls, asgi (Starlette: /ws + Django)
├── domain/               Reglas de negocio. Sin Twilio, sin Telegram, sin HTTP
│   ├── entities/         Account, Business, Order (modelos con sus reglas)
│   ├── repositories/     Interfaces de persistencia (ABC) + Repositories
│   ├── services/         Interfaces de servicios externos: llamadas, mensajes, IA, verificación, tokens
│   ├── rules/            Funciones puras: teléfonos, límites de llamadas, respuestas sí/no, idiomas
│   ├── exceptions.py     Errores de negocio con su status_code y mensaje para la persona
│   └── migrations/
├── application/          Casos de uso
│   ├── commands/<caso>/  command.py + command_dto.py   → cambian el estado
│   ├── queries/<caso>/   query.py + query_dto.py       → solo leen
│   └── shared/live_calls.py  Llamadas en curso (seguras entre hilos)
├── infrastructure/       Adaptadores
│   ├── api/<endpoint>/   view.py (router Ninja) + schema.py
│   ├── webhooks/         Twilio y Telegram (con su propia verificación)
│   ├── voice/            Agente de voz Pipecat + WebSocket del audio
│   ├── repositories/     django_*_repository.py
│   ├── services/         Twilio, Telegram, Google Places, Ollama, JWT
│   ├── management/       check_config, setup_telegram, ensure_admin
│   ├── dependencies.py   Qué implementación real usa cada puerto
│   └── admin.py          Panel /admin
└── tests/                domain, application (commands, queries) e infrastructure (API)
```

**Comandos:** register_account, log_in, update_profile, create_telegram_link, propose_business,
review_business, place_order, answer_question, hang_up, record_call_status,
handle_answering_machine, handle_telegram_message, handle_telegram_button.

**Consultas:** authenticate_token, get_profile, search_businesses, list_businesses_by_status,
interpret_order, list_orders, get_order, authorize_voice_stream.

## Arrancar en PyCharm (Mac)

1. *File → Open* → elige la carpeta **`backend`**.
2. Intérprete: usa un entorno virtual con Python 3.12 (por ejemplo el `venv` que ya tienes en la carpeta
   del proyecto, como en alma-estetica). Con el entorno activado, instala con Poetry:
   ```bash
   source ../venv/bin/activate     # o el entorno que use PyCharm
   pip install "poetry>=2,<3"      # o: brew install poetry
   poetry install
   ```
   `poetry.toml` trae `create = false`: Poetry instala en el entorno que tengas activado, igual que en
   alma-estetica, en Render y en Docker.
3. Copia `.env.example` como `.env` y rellena lo que tengas. Con todo vacío ya arranca.
4. Crea la base de datos y arranca:
   ```bash
   python manage.py migrate
   uvicorn core.asgi:application --reload --port 8000
   ```
   En PyCharm puedes crear una configuración *Python* con *module* `uvicorn` y parámetros
   `core.asgi:application --reload --port 8000`.
5. Abre **http://localhost:8000/api/docs**: la documentación interactiva de la API.
   Para probar los endpoints con sesión, pulsa *Authorize* y pega el token de `/api/auth/login`.
6. Panel de administración: pon `DJANGO_ADMIN_USER` y `DJANGO_ADMIN_PASSWORD` en el `.env`,
   ejecuta `python manage.py ensure_admin` y entra en **http://localhost:8000/admin**.

## Tests

```bash
pytest
ruff check .
```

Los tests usan SQLite y versiones falsas de Twilio, Telegram, Google y la IA (`tests/fakes.py`).

## Comandos útiles

| Comando | Para qué |
|---|---|
| `python manage.py check_config` | Dice qué variables faltan para poder llamar |
| `python manage.py setup_telegram` | Registra el webhook del bot en `PUBLIC_URL` |
| `python manage.py ensure_admin` | Crea el usuario del panel `/admin` |
| `sh start.sh` | Lo que hace Render al arrancar |

## Llamadas de verdad en local

Twilio y Telegram tienen que poder llegar a tu Mac: `ngrok http 8000`, pon esa URL en
`PUBLIC_URL`, reinicia y ejecuta `python manage.py setup_telegram`.
