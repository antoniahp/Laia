"""Aquí se decide qué implementación real usa cada repositorio y cada servicio. Los tests usan versiones falsas."""

from application.shared.live_audio import live_audio
from application.shared.live_calls import live_calls
from infrastructure.background import run_in_background
from infrastructure.repositories.django_repositories import build_django_repositories
from infrastructure.services.google_places_service import GooglePlacesService
from infrastructure.services.jwt_token_service import JwtTokenService
from infrastructure.services.ollama_language_model_service import OllamaLanguageModelService
from infrastructure.services.telegram_message_service import TelegramMessageService
from infrastructure.services.twilio_call_service import TwilioCallService


def get_repositories():
    return build_django_repositories()


def get_token_service():
    return JwtTokenService()


def get_message_service():
    return TelegramMessageService()


def get_call_service():
    return TwilioCallService()


def get_verification_service():
    return GooglePlacesService()


def get_place_search_service():
    return GooglePlacesService()


def get_language_model_service():
    return OllamaLanguageModelService()


def get_live_calls():
    return live_calls


def get_background_runner():
    return run_in_background


def get_live_audio():
    return live_audio
