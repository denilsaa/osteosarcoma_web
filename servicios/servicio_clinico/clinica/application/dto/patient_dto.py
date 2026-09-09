from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID


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

    # ======================================================
    # CONTACTOS DEL PACIENTE
    # ======================================================

    mobile_phone: Optional[str] = None

    landline_phone: Optional[str] = None

    email: Optional[str] = None

    # ======================================================
    # CONTACTO DE EMERGENCIA
    # ======================================================

    emergency_contact_name: Optional[str] = None

    emergency_relationship: Optional[str] = None

    emergency_phone: Optional[str] = None

    emergency_email: Optional[str] = None


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