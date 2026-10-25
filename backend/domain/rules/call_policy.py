"""Límites para evitar abusos y gastos."""

from domain.exceptions import CallInProgress, DailyLimitReached


def ensure_can_call(account, calls_today, has_call_in_progress, max_calls_per_day):
    if has_call_in_progress:
        raise CallInProgress()
    if not account.is_admin and calls_today >= max_calls_per_day:
        raise DailyLimitReached(f"Has llegado al límite de {max_calls_per_day} llamadas por hoy.")
