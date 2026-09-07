from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FieldChangeDTO:
    field: str

    old_value: Optional[str]

    new_value: Optional[str]