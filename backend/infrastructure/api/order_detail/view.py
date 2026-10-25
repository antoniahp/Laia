from uuid import UUID

from ninja import Router

from application.queries.get_order.query import GetOrderQuery
from application.queries.get_order.query_dto import GetOrderQueryDTO
from infrastructure import dependencies
from infrastructure.api.shared.schemas import OrderSchema

router = Router(tags=["pedidos"])


@router.get("/orders/{order_id}", response=OrderSchema)
def get_order(request, order_id: UUID):
    return GetOrderQuery(dependencies.get_repositories()).execute(GetOrderQueryDTO(account_id=request.auth.id, order_id=order_id))
