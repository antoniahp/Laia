from ninja import Router

from application.queries.interpret_order.query import InterpretOrderQuery
from application.queries.interpret_order.query_dto import InterpretOrderQueryDTO
from infrastructure import dependencies
from infrastructure.api.order_interpretation.schema import InterpretOrderSchema, OrderDraftSchema

router = Router(tags=["pedidos"])


@router.post("/parse", response=OrderDraftSchema)
def interpret_order(request, data: InterpretOrderSchema):
    query = InterpretOrderQuery(dependencies.get_repositories(), dependencies.get_language_model_service())
    parsed, business = query.execute(InterpretOrderQueryDTO(account_id=request.auth.id, **data.dict()))
    return {**parsed.__dict__, "business": business}
