"""API de la app (Django Ninja). Documentación interactiva en /api/docs."""

from ninja import NinjaAPI

from infrastructure.api.admin_businesses.view import router as admin_businesses
from infrastructure.api.auth_login.view import router as auth_login
from infrastructure.api.auth_register.view import router as auth_register
from infrastructure.api.authentication import JwtAuthentication
from infrastructure.api.businesses.view import router as businesses
from infrastructure.api.current_user.view import router as current_user
from infrastructure.api.exception_handler import register_exception_handlers
from infrastructure.api.legal.view import router as legal
from infrastructure.api.order_actions.view import router as order_actions
from infrastructure.api.order_detail.view import router as order_detail
from infrastructure.api.order_interpretation.view import router as order_interpretation
from infrastructure.api.orders.view import router as orders

api = NinjaAPI(title="Laia", version="2.0", auth=JwtAuthentication(), urls_namespace="api")
register_exception_handlers(api)

for router in (
    auth_register,
    auth_login,
    current_user,
    businesses,
    admin_businesses,
    order_interpretation,
    orders,
    order_detail,
    order_actions,
    legal,
):
    api.add_router("", router)
