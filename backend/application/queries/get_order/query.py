from domain.exceptions import OrderNotFound


class GetOrderQuery:
    def __init__(self, repositories):
        self.repositories = repositories

    def execute(self, dto):
        order = self.repositories.orders.find_for_account(dto.account_id, dto.order_id)
        if not order:
            raise OrderNotFound()
        return order
