from uuid import UUID

from ninja import Router

from application.commands.answer_question.command import AnswerQuestionCommand
from application.commands.answer_question.command_dto import AnswerQuestionCommandDTO
from application.commands.hang_up.command import HangUpCommand
from application.commands.hang_up.command_dto import HangUpCommandDTO
from application.commands.transfer_call.command import TransferCallCommand
from application.commands.transfer_call.command_dto import TransferCallCommandDTO
from application.queries.get_order.query import GetOrderQuery
from application.queries.get_order.query_dto import GetOrderQueryDTO
from infrastructure import dependencies
from infrastructure.api.order_actions.schema import AnswerSchema
from infrastructure.api.shared.schemas import OrderSchema

router = Router(tags=["pedidos"])


def _order(request, order_id):
    return GetOrderQuery(dependencies.get_repositories()).execute(GetOrderQueryDTO(account_id=request.auth.id, order_id=order_id))


@router.post("/orders/{order_id}/answer", response=OrderSchema)
def answer(request, order_id: UUID, data: AnswerSchema):
    command = AnswerQuestionCommand(dependencies.get_repositories(), dependencies.get_live_calls())
    command.execute(AnswerQuestionCommandDTO(account_id=request.auth.id, order_id=order_id, answer=data.answer))
    return _order(request, order_id)


@router.post("/orders/{order_id}/hangup", response=OrderSchema)
def hang_up(request, order_id: UUID):
    command = HangUpCommand(dependencies.get_repositories(), dependencies.get_call_service(), dependencies.get_live_calls())
    command.execute(HangUpCommandDTO(account_id=request.auth.id, order_id=order_id))
    return _order(request, order_id)


@router.post("/orders/{order_id}/transfer", response=OrderSchema)
def transfer(request, order_id: UUID):
    """«Hablar yo»: Laia avisa al negocio y te pasa la llamada a tu móvil."""
    command = TransferCallCommand(dependencies.get_repositories(), dependencies.get_call_service(), dependencies.get_live_calls())
    command.execute(TransferCallCommandDTO(account_id=request.auth.id, order_id=order_id))
    return _order(request, order_id)
