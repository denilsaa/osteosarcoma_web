from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ClinicalCaseStatus:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class ClinicalCasePriority:
    id: int
    code: str
    name: str
    level: int


@dataclass(frozen=True)
class ClinicalCase:
    id_case: UUID
    patient_id: UUID
    code: str
    status: ClinicalCaseStatus
    priority: ClinicalCasePriority
    responsible_oncologist_uuid: UUID | None
    opening_date: datetime
    closing_date: datetime | None
    consultation_reason: str
    general_observation: str | None