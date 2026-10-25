from dataclasses import dataclass

from domain.repositories.account_repository import AccountRepository
from domain.repositories.business_repository import BusinessRepository
from domain.repositories.order_repository import OrderRepository


@dataclass(frozen=True)
class Repositories:
    """Todos los repositorios juntos, para pasarlos a los commands y queries con un solo parámetro."""

    accounts: AccountRepository
    businesses: BusinessRepository
    orders: OrderRepository
