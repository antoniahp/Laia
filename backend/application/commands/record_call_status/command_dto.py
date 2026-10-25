from dataclasses import dataclass


@dataclass(frozen=True)
class RecordCallStatusCommandDTO:
    order_id: str
    call_status: str
