class SearchBusinessesQuery:
    """Negocios verificados, más los que ha propuesto esta persona (para que vea su estado)."""

    def __init__(self, repositories):
        self.repositories = repositories

    def execute(self, dto):
        return self.repositories.businesses.search_visible(dto.account_id, (dto.search or "").strip())
