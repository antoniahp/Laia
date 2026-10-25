from ninja import Router

from application.commands.place_order.command import PlaceOrderCommand
from application.commands.place_order.command_dto import PlaceOrderCommandDTO
from application.queries.list_orders.query import ListOrdersQuery
from application.queries.list_orders.query_dto import ListOrdersQueryDTO
from infrastructure import dependencies
from infrastructure.api.orders.schema import PlaceOrderSchema
from infrastructure.api.shared.schemas import OrderSchema

router = Router(tags=["pedidos"])


@router.get("/orders", response=list[OrderSchema])
def list_orders(request):
    return ListOrdersQuery(dependencies.get_repositories()).execute(ListOrdersQueryDTO(account_id=request.auth.id))


@router.post("/orders", response=OrderSchema)
def place_order(request, data: PlaceOrderSchema):
    command = PlaceOrderCommand(
        dependencies.get_repositories(),
        dependencies.get_call_service(),
        dependencies.get_message_service(),
        dependencies.get_live_calls(),
        dependencies.get_background_runner(),
        place_search_service=dependencies.get_place_search_service(),
        language_model_service=dependencies.get_language_model_service(),
    )
    return command.execute(PlaceOrderCommandDTO(account_id=request.auth.id, **data.dict()))
