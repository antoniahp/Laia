# Laia 🍕📞

**Alexa para todo lo que no está en Amazon.**
Le dices a Laia qué quieres y ella llama al negocio por ti, en su idioma, sigue tus reglas
("si no hay cuatro quesos, pide margarita", "máximo 20 €") y solo te pregunta cuando hace falta,
por la app o por Telegram.

Proyecto para el reto Hacktoberfest 2026 de DEV, semana 3: *Slow and Steady*.

## Qué hace

| Pestaña | Para qué |
|---|---|
| **Pedir** | «Pide una cuatro quesos en Tres Hermanas, si no hay margarita, máximo 20 €». Laia entiende la frase, busca el sitio en Google Maps y llama. |
| **Extranjero** | Eliges país y sitio, le dices en español qué quieres («reserva mesa para 2 el viernes»). Laia llama en su idioma y te traduce cada frase. |
| **Llamadas** | Todo lo que ha hecho Laia, con el resultado. |
| **Perfil** | Tus datos, Telegram, descargar tus datos, borrar la cuenta y los textos legales. |

Durante la llamada puedes:
- **Escuchar** la conversación en directo desde la app (audio del negocio y de Laia, sin grabar).
- **Responder** sus dudas con un toque («No hay cuatro quesos, ¿margarita?» → Sí / No / otra cosa), también por Telegram.
- **Hablar yo**: Laia avisa al negocio y te pasa la llamada a tu móvil.
- **Colgar**.

Tres modos: **pedir** (comida a domicilio, pagas tú en la entrega), **reservar** (mesa, cita, hotel) y **preguntar** (precio, horario, si tienen algo).

> ¿Por qué no llama desde tu propio teléfono, como «Ok Google, llama a mamá»? Android no deja que una app
> hable con su propia voz dentro de una llamada normal. Por eso Laia llama desde la nube (Twilio) y tú la
> escuchas en la app o te la pasa cuando quieras.

## Cómo funciona

```
App Flutter (Android)              Backend Django Ninja                      Fuera
  «Oye Laia, pide...»         ─►   Gemma entiende la orden  ─────────────►  Ollama Cloud (open-weight)
  Elige el sitio              ─►   Busca en Google Maps  ────────────────►  Google Places
  Revisas y pulsas Llamar     ─►   Comprueba reglas y límites
                                   Twilio llama  ────────────────────────►  El negocio
                                     ├─ Oído: Whisper o ElevenLabs Scribe
                                     ├─ Cerebro: Gemma + herramientas
                                     ├─ Reglas en código: precio y alternativas
                                     ├─ Voz: ElevenLabs (en el idioma del negocio)
                                     └─ Traducción al español: Gemma
  Escuchar en directo         ◄─   Copia del audio (no se graba)
  Conversación y dudas        ◄─   App + Telegram
  Hablar yo                   ─►   Twilio te pasa la llamada a tu móvil
```

**Legal y privacidad (RGPD, AI Act art. 50)**
- Laia empieza siempre con «Hola, soy la IA y llamo para…» en el idioma del negocio. Si le preguntan, dice la verdad.
- No se graba el audio. Las conversaciones se borran a los 30 días (`RETENTION_DAYS`); el resultado se queda.
- Para crear cuenta hay que ser mayor de edad y aceptar condiciones y privacidad (se guarda la versión aceptada).
- Desde la app: descargar tus datos y borrar la cuenta al momento.
- Páginas públicas: `/legal/privacidad/`, `/legal/terminos/` y `/legal/negocios/` (con la forma de pedir no recibir llamadas).
- De Google Maps solo se guarda el identificador del sitio; nombre, dirección y teléfono se piden al momento, y la app muestra «Google Maps» junto a los resultados.
- Rellena `LEGAL_OWNER_NAME` y `LEGAL_CONTACT_EMAIL` en el `.env` antes de abrirlo a otras personas.

**Seguridad y abusos**
- Cuentas con email y contraseña (hash de Django + JWT). Cada persona solo ve y escucha sus llamadas.
- Código de invitación opcional para registrarse (`SIGNUP_CODE`).
- Solo llama a negocios verificados: los de Google Maps (abiertos y con teléfono) o los que apruebas tú por Telegram.
- Nunca llama a números de tarificación especial (806, 905, 902...) ni a países no permitidos (`ALLOWED_COUNTRIES`).
- Límite de llamadas al día por persona, una llamada a la vez, máximo 10 minutos.
- Las peticiones de Twilio se verifican con su firma, y el audio de cada llamada exige un secreto único.
- Nunca da datos de pago.

**Situaciones difíciles**
- Contestador automático: Twilio lo detecta y Laia cuelga y te avisa.
- Menús de teclas («pulse 1»): se guardan por negocio y Twilio las marca al conectar.
- No entiende: pide que repitan; a la segunda, te pregunta a ti. O pulsas «Hablar yo».
- Música de espera: espera hasta 2,5 minutos de silencio antes de colgar.

```
laia/
├── backend/           Servidor: Django + Django Ninja, hexagonal con CQRS, Poetry (ver backend/README.md)
├── app/               App Android (Flutter)
├── render.yaml        Despliegue en Render con un clic
├── GUIA_ALTA.md       Alta paso a paso en cada servicio
└── demo/              Demo visual del flujo
```

---

## 1. Darse de alta y desplegar

Sigue **[GUIA_ALTA.md](GUIA_ALTA.md)**: GitHub, Ollama, ElevenLabs, Telegram, Twilio,
Google (opcional) y Render. Al final tendrás el servidor funcionando en una URL tuya.

## 2. Compilar la app

Necesitas Flutter instalado (https://docs.flutter.dev/get-started/install, sección Android)
y `flutter doctor` en verde.

```bash
cd laia/app
flutter create --org com.laia --project-name laia --platforms android .
cp android_config/AndroidManifest.xml android/app/src/main/AndroidManifest.xml
rm -f test/widget_test.dart
```

Abre `lib/config.dart` y pon tu URL de Render:

```dart
const kDefaultServerUrl = 'https://laia-backend-xxxx.onrender.com';
```

Para probar en tu móvil conectado por USB (con la depuración USB activada):

```bash
flutter pub get
flutter run
```

## 3. Publicar el APK para que lo prueben desde DEV

La app no va a Google Play: se descarga directamente.

```bash
flutter build apk --release
```

El archivo queda en `build/app/outputs/flutter-apk/app-release.apk`.

1. En GitHub, ve a tu repositorio → *Releases → Draft a new release*.
2. Etiqueta `v1.0`, título "Laia 1.0", arrastra el `app-release.apk` y publica.
3. En el post de DEV enlaza la release. Explica a quien la pruebe que:
   - Android pedirá permiso para *instalar apps de origen desconocido*.
   - Necesita el **código de invitación** para crear cuenta (si has puesto `SIGNUP_CODE`).
   - Solo puede llamar a negocios verificados.

**Importante para las pruebas de otras personas:** no verifiques negocios reales solo para probar,
o la pizzería de tu barrio recibirá llamadas de desconocidos. Crea un negocio de prueba
("Pizzería Demo") con un número tuyo o de un amigo que sepa que va a recibir llamadas
(pestaña Perfil → Mis sitios → Proponer, y lo apruebas por Telegram o en `/admin`).

El APK de `flutter build apk` va firmado con una clave de depuración. Vale para que lo instalen
a mano, pero si un día quieres publicar en Google Play tendrás que firmarlo con tu propia clave.

## 4. Administrar

Tu cuenta es administradora si te registras con el email de `ADMIN_EMAIL`.

- **Negocios nuevos:** te llegan por Telegram con botones *Verificar* / *Rechazar*.
- **Menús de teclas:** si un negocio tiene contestador con menú, guarda las teclas.
  `w` es una pausa de medio segundo. Por ejemplo, esperar 1,5 s y pulsar 1 es `www1`:
  ```bash
  curl -X POST https://laia-backend-xxxx.onrender.com/api/admin/businesses/ID \
    -H "Authorization: Bearer TU_TOKEN" -H "Content-Type: application/json" \
    -d '{"ivr_digits": "www1"}'
  ```
  Tu token lo devuelve `POST /api/auth/login`.
- **Pendientes:** `GET /api/admin/businesses` lista los que esperan revisión.
- **Panel de Django:** en `/admin` puedes verificar negocios, poner teclas de menú y ver pedidos.

## 5. Desarrollo en local

```bash
make run            # backend en http://localhost:8000 (con el entorno virtual en ./venv)
make run flutter    # la app en el móvil conectado
make test           # tests del backend
```

Todo lo del backend (PyCharm, Poetry, tests, comandos) está en **[backend/README.md](backend/README.md)**.

Además de la app y Telegram, puedes administrar negocios y ver pedidos en el panel de Django: `/admin`.

## Qué falta para una versión pública

- Varias instancias del servidor: hoy las llamadas en curso viven en la memoria de un único servidor.
- Pantalla de administración dentro de la app (ahora es por Telegram, /admin y API).
- Revisión de los textos legales por un abogado y registro de actividades de tratamiento (RGPD art. 30).
- Firmar el APK con tu propia clave si algún día va a Google Play.

## Licencia

MIT
