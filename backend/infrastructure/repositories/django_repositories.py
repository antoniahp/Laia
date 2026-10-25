from domain.repositories.repositories import Repositories
from infrastructure.repositories.django_account_repository import DjangoAccountRepository
from infrastructure.repositories.django_business_repository import DjangoBusinessRepository
from infrastructure.repositories.django_order_repository import DjangoOrderRepository


def build_django_repositories():
    return Repositories(
        accounts=DjangoAccountRepository(),
        businesses=DjangoBusinessRepository(),
        orders=DjangoOrderRepository(),
    )
