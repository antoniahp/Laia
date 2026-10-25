class ListOrdersQuery:
    def __init__(self, repositories):
        self.repositories = repositories

    def execute(self, dto):
        return self.repositories.orders.list_for_account(dto.account_id)
