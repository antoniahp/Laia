from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AnswerQuestionCommandDTO:
    account_id: UUID
    order_id: UUID
    answer: str
