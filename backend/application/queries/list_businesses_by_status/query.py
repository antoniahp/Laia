from domain.entities import Business
from domain.exceptions import InvalidReview, SessionExpired


class ListBusinessesByStatusQuery:
    def __init__(self, repositories):
        self.repositories = repositories

    def execute(self, dto):
        admin = self.repositories.accounts.find(dto.admin_id)
        if not admin:
            raise SessionExpired()
        admin.require_admin()
        if dto.status not in dict(Business.STATUSES):
            raise InvalidReview()
        return self.repositories.businesses.list_by_status(dto.status)
