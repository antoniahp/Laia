"""Avisos de la compañía telefónica (Twilio). Se comprueba su firma en cada petición."""

from django.conf import settings
from ninja import Router
from ninja.errors import HttpError

from application.commands.handle_answering_machine.command import HandleAnsweringMachineCommand
from application.commands.handle_answering_machine.command_dto import HandleAnsweringMachineCommandDTO
from application.commands.record_call_status.command import RecordCallStatusCommand
from application.commands.record_call_status.command_dto import RecordCallStatusCommandDTO
from infrastructure import dependencies

router = Router(tags=["webhooks"])


def _authentic_params(request, call_service):
    params = {key: request.POST.get(key) for key in request.POST}
    url = settings.LAIA["PUBLIC_URL"] + request.path
    if not call_service.is_request_authentic(url, params, request.headers.get("X-Twilio-Signature", "")):
        raise HttpError(403, "Firma de Twilio no válida")
    return params


@router.post("/twilio/status/{order_id}")
def call_status(request, order_id: str):
    params = _authentic_params(request, dependencies.get_call_service())
    command = RecordCallStatusCommand(dependencies.get_live_calls(), dependencies.get_repositories())
    command.execute(RecordCallStatusCommandDTO(order_id=order_id, call_status=params.get("CallStatus", "")))
    return {}


@router.post("/twilio/amd/{order_id}")
def answering_machine(request, order_id: str):
    call_service = dependencies.get_call_service()
    params = _authentic_params(request, call_service)
    command = HandleAnsweringMachineCommand(call_service, dependencies.get_live_calls())
    command.execute(
        HandleAnsweringMachineCommandDTO(order_id=order_id, answered_by=params.get("AnsweredBy", ""), call_id=params.get("CallSid", ""))
    )
    return {}
