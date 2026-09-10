from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID


# ==========================================================
# CONTACTO DEL PACIENTE
# ==========================================================


@dataclass(frozen=True)
class CreatePatientContactDTO:
    contact_type_id: int

    value: str

    primary: bool = False


# ==========================================================
# CONTACTO DE EMERGENCIA
# ==========================================================


@dataclass(frozen=True)
class CreateEmergencyContactDTO:
    full_name: str

    relationship: str

    phone: str

    email: Optional[str] = None

    primary: bool = False


# ==========================================================
# CREAR PACIENTE
# ==========================================================


@dataclass(frozen=True)
class CreatePatientDTO:
    first_names: str

    paternal_surname: str

    maternal_surname: Optional[str]

    birth_date: date

    sex_id: int

    document_type_id: int

    document_number: str

    complement: Optional[str] = None

    issued_in: Optional[str] = None

    contacts: list[
        CreatePatientContactDTO
    ] = field(
        default_factory=list
    )

    emergency_contacts: list[
        CreateEmergencyContactDTO
    ] = field(
        default_factory=list
    )


# ==========================================================
# ACTUALIZAR PACIENTE
# ==========================================================


@dataclass(frozen=True)
class UpdatePatientDTO:
    patient_id: UUID

    reason: str

    first_names: Optional[str] = None

    paternal_surname: Optional[str] = None

    maternal_surname: Optional[str] = None

    birth_date: Optional[date] = None

    sex_id: Optional[int] = None

    active: Optional[bool] = None


# ==========================================================
# FILTROS
# ==========================================================


@dataclass(frozen=True)
class PatientFiltersDTO:
    search: Optional[str] = None

    sex_code: Optional[str] = None

    active: Optional[bool] = None

    document_type_code: Optional[str] = None

    page: int = 1

    page_size: int = 10


# ==========================================================
# POSIBLES DUPLICADOS
# ==========================================================


@dataclass(frozen=True)
class PossibleDuplicateDTO:
    document_type_id: Optional[int] = None

    document_number: Optional[str] = None

    first_names: Optional[str] = None

    paternal_surname: Optional[str] = None

    maternal_surname: Optional[str] = None

    birth_date: Optional[date] = None