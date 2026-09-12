from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class CreateClinicalCaseDTO:
    patient_id: UUID

    priority_id: int

    responsible_oncologist_uuid: UUID

    consultation_reason: str

    general_observation: Optional[str] = None


@dataclass(frozen=True)
class ClinicalCaseFiltersDTO:
    search: Optional[str] = None

    status_code: Optional[str] = None

    priority_code: Optional[str] = None

    patient_id: Optional[UUID] = None

    responsible_oncologist_uuid: Optional[UUID] = None

    opening_date: Optional[date] = None

    page: int = 1

    page_size: int = 10


@dataclass(frozen=True)
class CreateClinicalAntecedentDTO:
    case_id: UUID

    antecedent_type_id: int

    description: str


@dataclass(frozen=True)
class CreateClinicalSymptomDTO:
    case_id: UUID

    symptom_id: int

    intensity_id: Optional[int] = None

    start_date: Optional[date] = None

    observation: Optional[str] = None


@dataclass(frozen=True)
class CreateClinicalSignDTO:
    case_id: UUID

    sign_id: int

    finding_description: Optional[str] = None


@dataclass(frozen=True)
class CreateClinicalObservationDTO:
    case_id: UUID

    content: str