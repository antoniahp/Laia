from domain.exceptions import EmptyAnswer, NotWaitingForAnswer, OrderNotFound


class AnswerQuestionCommand:
    """Respondes desde la app a una duda de Laia en mitad de la llamada."""

    def __init__(self, repositories, live_calls):
        self.repositories = repositories
        self.live_calls = live_calls

    def execute(self, dto):
        answer = (dto.answer or "").strip()
        if not answer:
            raise EmptyAnswer()
        if not self.repositories.orders.find_for_account(dto.account_id, dto.order_id):
            raise OrderNotFound()
        call = self.live_calls.get(dto.order_id)
        if not call or not call.answer(answer):
            raise NotWaitingForAnswer()
        call.flush()
