from uuid import UUID

from ninja import Router

from application.commands.review_business.command import ReviewBusinessCommand
from application.commands.review_business.command_dto import ReviewBusinessCommandDTO
from application.queries.list_businesses_by_status.query import ListBusinessesByStatusQuery
from application.queries.list_businesses_by_status.query_dto import ListBusinessesByStatusQueryDTO
from infrastructure import dependencies
from infrastructure.api.admin_businesses.schema import ReviewBusinessSchema
from infrastructure.api.shared.schemas import BusinessAdminSchema, BusinessSchema

router = Router(tags=["administración"])


@router.get("/admin/businesses", response=list[BusinessAdminSchema])
def list_businesses(request, status: str = "pendiente"):
    query = ListBusinessesByStatusQuery(dependencies.get_repositories())
    return query.execute(ListBusinessesByStatusQueryDTO(admin_id=request.auth.id, status=status))


@router.post("/admin/businesses/{business_id}", response=BusinessSchema)
def review_business(request, business_id: UUID, data: ReviewBusinessSchema):
    command = ReviewBusinessCommand(dependencies.get_repositories(), dependencies.get_message_service())
    return command.execute(ReviewBusinessCommandDTO(admin_id=request.auth.id, business_id=business_id, **data.dict()))
