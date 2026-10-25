"""Configuración de Django para Laia. Todo se lee de variables de entorno (archivo .env en local)."""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=""):
    """Como os.getenv, pero una variable vacía ("NOMBRE=") cuenta como no puesta."""
    return os.getenv(name, "").strip() or default


def env_bool(name, default):
    return env(name, str(default)).lower() in ("1", "true", "yes", "si", "sí")


def env_list(name, default):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "solo-para-desarrollo-cambiame-en-produccion-0123456789")
DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.ngrok-free.app,.ngrok-free.dev,.ngrok.app,.ngrok.dev")
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ninja",
    "domain.apps.DomainConfig",
    "infrastructure.apps.InfrastructureConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
ASGI_APPLICATION = "core.asgi.application"
WSGI_APPLICATION = "core.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "infrastructure" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# Sin DATABASE_URL usa SQLite (db.sqlite3). En Render se rellena sola con Postgres.
DATABASE_URL = env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, conn_health_checks=True)}

LANGUAGE_CODE = "es-es"
TIME_ZONE = env("TIME_ZONE", "Europe/Madrid")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# La URL pública (ngrok en local) siempre se acepta, sea cual sea su dominio
_PUBLIC_URL = env("PUBLIC_URL").rstrip("/")
if _PUBLIC_URL.startswith(("http://", "https://")):
    ALLOWED_HOSTS.append(_PUBLIC_URL.split("://", 1)[1].split("/")[0].split(":")[0])
    CSRF_TRUSTED_ORIGINS.append(_PUBLIC_URL)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}

# ---------------------------------------------------------------- Laia

LAIA = {
    # Cuentas
    "ADMIN_EMAIL": env("ADMIN_EMAIL").lower(),
    "SIGNUP_CODE": env("SIGNUP_CODE"),
    "MAX_CALLS_PER_DAY": int(env("MAX_CALLS_PER_DAY", "5")),
    "ALLOWED_COUNTRIES": [c.upper() for c in env_list("ALLOWED_COUNTRIES", "ES,DE,FR,IT,PT,GB,IE,NL,BE,AT")],
    # URL pública (ngrok en local; en Render se rellena sola)
    "PUBLIC_URL": (env("PUBLIC_URL") or env("RENDER_EXTERNAL_URL")).rstrip("/"),
    # Twilio
    "TWILIO_ACCOUNT_SID": env("TWILIO_ACCOUNT_SID"),
    "TWILIO_AUTH_TOKEN": env("TWILIO_AUTH_TOKEN"),
    "TWILIO_FROM_NUMBER": env("TWILIO_FROM_NUMBER"),
    "ENABLE_AMD": env_bool("ENABLE_AMD", True),
    "VALIDATE_TWILIO_SIGNATURE": env_bool("VALIDATE_TWILIO_SIGNATURE", True),
    # ElevenLabs
    "ELEVENLABS_API_KEY": env("ELEVENLABS_API_KEY"),
    "ELEVENLABS_VOICE_ID": env("ELEVENLABS_VOICE_ID"),
    "ELEVENLABS_MODEL": env("ELEVENLABS_MODEL", "eleven_flash_v2_5"),
    # Cerebro: Gemma vía Ollama (local u Ollama Cloud)
    "OLLAMA_HOST": env("OLLAMA_HOST", "https://ollama.com").rstrip("/"),
    "OLLAMA_MODEL": env("OLLAMA_MODEL", "gemma4:31b"),
    "OLLAMA_API_KEY": env("OLLAMA_API_KEY"),
    # Oído: whisper (open source, en el servidor) o elevenlabs (nube)
    "STT_PROVIDER": env("STT_PROVIDER", "whisper").lower(),
    "WHISPER_MODEL": env("WHISPER_MODEL", "small"),
    "WHISPER_DEVICE": env("WHISPER_DEVICE", "auto"),
    # Telegram
    "TELEGRAM_BOT_TOKEN": env("TELEGRAM_BOT_TOKEN"),
    "TELEGRAM_BOT_USERNAME": env("TELEGRAM_BOT_USERNAME").lstrip("@"),
    "TELEGRAM_WEBHOOK_SECRET": env("TELEGRAM_WEBHOOK_SECRET"),
    # Google Places
    "GOOGLE_PLACES_API_KEY": env("GOOGLE_PLACES_API_KEY"),
    # Legal: quién ofrece el servicio, versión de las condiciones y cuántos días se guardan las conversaciones
    "LEGAL_OWNER_NAME": env("LEGAL_OWNER_NAME", "[Nombre del responsable]"),
    "LEGAL_CONTACT_EMAIL": env("LEGAL_CONTACT_EMAIL") or env("ADMIN_EMAIL", "[email de contacto]"),
    "TERMS_VERSION": env("TERMS_VERSION", "2026-10"),
    "RETENTION_DAYS": int(env("RETENTION_DAYS", "30")),
}
