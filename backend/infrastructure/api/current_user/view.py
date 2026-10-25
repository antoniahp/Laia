from ninja import Router

from application.commands.create_telegram_link.command import CreateTelegramLinkCommand
from application.commands.create_telegram_link.command_dto import CreateTelegramLinkCommandDTO
from application.commands.delete_account.command import DeleteAccountCommand
from application.commands.delete_account.command_dto import DeleteAccountCommandDTO
from application.commands.update_profile.command import UpdateProfileCommand
from application.commands.update_profile.command_dto import UpdateProfileCommandDTO
from application.queries.export_my_data.query import ExportMyDataQuery
from application.queries.export_my_data.query_dto import ExportMyDataQueryDTO
from application.queries.get_profile.query import GetProfileQuery
from application.queries.get_profile.query_dto import GetProfileQueryDTO
from infrastructure import dependencies
from infrastructure.api.current_user.schema import TelegramLinkSchema, UpdateProfileSchema
from infrastructure.api.shared.schemas import AccountSchema

router = Router(tags=["cuentas"])


@router.get("/me", response=AccountSchema)
def me(request):
    return GetProfileQuery(dependencies.get_repositories()).execute(GetProfileQueryDTO(account_id=request.auth.id))


@router.patch("/me", response=AccountSchema)
def update_me(request, data: UpdateProfileSchema):
    command = UpdateProfileCommand(dependencies.get_repositories())
    return command.execute(UpdateProfileCommandDTO(account_id=request.auth.id, **data.dict()))


@router.post("/me/telegram", response=TelegramLinkSchema)
def telegram_link(request):
    command = CreateTelegramLinkCommand(dependencies.get_repositories(), dependencies.get_message_service())
    return {"url": command.execute(CreateTelegramLinkCommandDTO(account_id=request.auth.id))}


@router.get("/me/export")
def export_my_data(request):
    """Todo lo que Laia guarda de ti (RGPD: acceso y portabilidad)."""
    return ExportMyDataQuery(dependencies.get_repositories()).execute(ExportMyDataQueryDTO(account_id=request.auth.id))


@router.delete("/me", response={204: None})
def delete_me(request):
    """Borra tu cuenta, tus pedidos y tus conversaciones (RGPD: supresión)."""
    DeleteAccountCommand(dependencies.get_repositories(), dependencies.get_live_calls()).execute(
        DeleteAccountCommandDTO(account_id=request.auth.id)
    )
    return 204, None
