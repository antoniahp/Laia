from dataclasses import dataclass


@dataclass(frozen=True)
class HandleAnsweringMachineCommandDTO:
    order_id: str
    answered_by: str
    call_id: str = ""
