from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AddGoogleBusinessCommandDTO:
    account_id: UUID
    google_place_id: str
    label: str  # cómo lo llama la persona ("Tres Hermanas")
