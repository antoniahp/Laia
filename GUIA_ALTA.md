# Guía de alta: cuentas que necesita Laia

Haz los pasos en este orden. Apunta cada clave en un sitio seguro (un gestor de contraseñas):
las pegarás en Render al final. Nunca las subas a GitHub.

| Servicio | Para qué | ¿Obligatorio? | Coste aproximado |
|---|---|---|---|
| GitHub | Guardar el código y publicar el APK | Sí | Gratis |
| Ollama | El cerebro (Gemma 4) | Sí | Mira ollama.com/pricing |
| ElevenLabs | La voz (y el oído si no usas Whisper) | Sí | Tu mes gratis, luego según plan |
| Twilio | Las llamadas | Sí | Por minuto de llamada + número mensual |
| Telegram | Dudas y avisos de Laia | Muy recomendado | Gratis |
| Render | Servidor y base de datos | Sí | Desde 7 $/mes + Postgres |
| Google Cloud | Verificar negocios solos | Opcional | Tiene uso gratis mensual; requiere tarjeta |

---

## 1. GitHub (10 min)

1. Crea cuenta en https://github.com si no la tienes.
2. Crea un repositorio nuevo llamado `laia` (público, para que el jurado lo vea).
3. Sube el proyecto. Desde la carpeta `laia/` en tu Mac:
   ```bash
   git init
   git add .
   git commit -m "Laia"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/laia.git
   git push -u origin main
   ```
   El archivo `.gitignore` ya evita que se suba tu `.env`.

## 2. Ollama Cloud (5 min)

1. Crea cuenta en https://ollama.com
2. Ve a *Settings → Keys* y crea una clave.
3. Apunta: **OLLAMA_API_KEY**.
4. Revisa los límites de tu plan en https://ollama.com/pricing antes de grabar la demo.

## 3. ElevenLabs (5 min)

1. Entra en https://elevenlabs.io y activa tu mes gratis.
2. *Developers → API Keys*: crea una clave con permisos de *Text to Speech* y *Speech to Text*.
   Apunta: **ELEVENLABS_API_KEY**.
3. *Voices*: elige una voz que suene bien en varios idiomas, ábrela y copia su ID.
   Apunta: **ELEVENLABS_VOICE_ID**.

## 4. Telegram (5 min)

1. En Telegram, abre un chat con **@BotFather**.
2. Escribe `/newbot`, ponle nombre (por ejemplo *Laia*) y un usuario acabado en `bot`
   (por ejemplo `laia_pedidos_bot`).
3. BotFather te da un token del tipo `123456:ABC...`. Apunta: **TELEGRAM_BOT_TOKEN**.
   Apunta también el usuario del bot sin @ (por ejemplo `laia_pedidos_bot`): **TELEGRAM_BOT_USERNAME**.
4. Opcional: `/setuserpic` para ponerle foto y `/setdescription` para describirlo.

No hace falta configurar nada más: el servidor registra el webhook solo al arrancar (`setup_telegram`).

## 5. Twilio (30 min, más la espera de la documentación)

### 5.1 Cuenta
1. Regístrate en https://www.twilio.com/try-twilio y verifica tu email y tu móvil.
2. En la consola, copia **Account SID** y **Auth Token**.
   Apunta: **TWILIO_ACCOUNT_SID** y **TWILIO_AUTH_TOKEN**.

### 5.2 Cuenta de prueba o de pago
- **Prueba (gratis):** solo puede llamar a números que verifiques en
  *Phone Numbers → Manage → Verified Caller IDs*, y al empezar cada llamada suena un aviso en inglés.
  Vale para tu demo con un amigo.
- **De pago:** necesaria si otras personas van a usar Laia. Pulsa *Upgrade* y añade saldo.

### 5.3 Número de teléfono
1. *Phone Numbers → Buy a number*. Elige país **España** y que tenga *Voice*.
2. Para números españoles Twilio pide un **Regulatory Bundle**: tu nombre, dirección en España y un documento
   de identidad. Rellénalo en *Phone Numbers → Regulatory Compliance*. Suele tardar uno o varios días
   en aprobarse, así que hazlo cuanto antes.
3. Mientras tanto puedes usar el número de prueba que te da Twilio.
4. Apunta el número con prefijo: **TWILIO_FROM_NUMBER** (por ejemplo `+34911234567`).

### 5.4 Permisos de países
*Voice → Settings → Geo permissions*: activa solo los países a los que Laia debe llamar
(España, Alemania...). Así, aunque alguien lo intentara, Twilio bloquearía llamadas a otros países.

## 6. Google Places (opcional, 15 min)

Sirve para verificar negocios automáticamente. Sin esta clave, los negocios nuevos te llegan
por Telegram para que los apruebes tú.

1. Entra en https://console.cloud.google.com y crea un proyecto `laia`.
2. Activa la facturación (pide tarjeta; hay uso gratuito mensual).
3. *APIs y servicios → Biblioteca*: activa **Places API (New)**.
4. *Credenciales → Crear credenciales → Clave de API*.
5. Restringe la clave: *Restricciones de API → Places API (New)*.
6. Pon un límite de gasto: *Facturación → Presupuestos y alertas*.
7. Apunta: **GOOGLE_PLACES_API_KEY**.

## 7. Render (20 min)

1. Crea cuenta en https://render.com con tu GitHub.
2. *New → Blueprint* y elige tu repositorio `laia`. Render lee `render.yaml` y te muestra:
   - un servicio web **laia-backend** (Django Ninja, instalado con Poetry)
   - una base de datos Postgres **laia-db**
3. Te pedirá los valores marcados como secretos. Pega los que has apuntado:
   - **ADMIN_EMAIL**: el email con el que te vas a registrar en la app. Esa cuenta será la de administradora.
   - **SIGNUP_CODE**: un código para que solo se registre quien tú quieras (por ejemplo `hacktober26`).
     Déjalo vacío si quieres registro abierto.
   - **DJANGO_ADMIN_USER** y **DJANGO_ADMIN_PASSWORD**: usuario y contraseña para el panel `/admin`.
   - El resto: Ollama, Twilio, ElevenLabs, Telegram (token y usuario del bot) y, si lo tienes, Google.
4. **Planes** (puedes cambiarlos en el panel de cada servicio, en *Settings → Instance type*):
   - Servicio web: el plan gratis se duerme a los 15 minutos sin uso y tarda un minuto en despertar.
     Para la demo usa como mínimo el de **512 MB (7 $/mes)**. Si quieres usar Whisper en vez de
     ElevenLabs para el oído, necesitas el de **2 GB (25 $/mes)** y cambiar `STT_PROVIDER` a `whisper`.
   - Base de datos: la gratis **se borra a los 30 días** (con 14 de margen). Pásala al plan de pago
     más pequeño antes de que caduque.
5. Pulsa *Apply*. La primera vez tarda unos minutos.
6. Copia la URL del servicio (por ejemplo `https://laia-backend-xxxx.onrender.com`) y abre
   `/api/docs` en el navegador: debe salir la documentación de la API. En `/admin` tienes el panel.

## 8. Primeros pasos con tu cuenta de administradora

1. En `app/lib/config.dart` pon tu URL de Render en `kDefaultServerUrl`.
2. Instala la app (ver README) y **crea tu cuenta con el email que pusiste en ADMIN_EMAIL**.
3. *Ajustes → Conectar Telegram* → pulsa *Iniciar* en el bot. Desde ahora te llegan los negocios a revisar.
4. *Negocios → Proponer*: añade la pizzería de prueba (el móvil de tu amigo). Te llegará a Telegram
   con botones para verificarla.
5. Rellena tu dirección en *Ajustes* y haz tu primer pedido.

## Si algo falla

En Render, abre el servicio **laia-backend → Logs**. Al arrancar, `check_config` dice qué variables faltan.
Los mensajes más habituales:

| Mensaje | Qué pasa |
|---|---|
| `Faltan para poder llamar: ...` | Falta alguna clave en *Environment*. |
| `Firma de Twilio no válida` | La URL pública no coincide. En Render no debería pasar; en local con ngrok, revisa `PUBLIC_URL`. |
| `Telegram no acepta la configuración` | El token del bot está mal copiado. |
| `Google Places falló` | La clave no tiene activada *Places API (New)* o no hay facturación. |
