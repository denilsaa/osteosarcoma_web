from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class PatientDocument:
    id_document: Optional[UUID]

    document_type_id: int
    document_type_code: str
    document_type_name: str

    document_number: str

    complement: Optional[str] = None
    issued_in: Optional[str] = None


@dataclass(frozen=True)
class PatientContact:
    id_contact: Optional[UUID]

    contact_type_id: int
    contact_type_code: str
    contact_type_name: str

    value: str
    primary: bool = False


@dataclass
class Patient:
    id_patient: Optional[UUID]

    first_names: str
    paternal_surname: str
    maternal_surname: Optional[str]

    birth_date: date

    sex_id: int
    sex_code: str
    sex_name: str

    active: bool = True

    registration_date: Optional[
        datetime
    ] = None

    documents: list[
        PatientDocument
    ] = field(
        default_factory=list
    )

    contacts: list[
        PatientContact
    ] = field(
        default_factory=list
    )

    clinical_cases_count: int = 0

    @property
    def full_name(
        self,
    ) -> str:
        parts = [
            self.first_names,
            self.paternal_surname,
            self.maternal_surname,
        ]

        return " ".join(
            part.strip()
            for part in parts
            if part
        )

    @property
    def primary_document(
        self,
    ) -> Optional[
        PatientDocument
    ]:
        if not self.documents:
            return None

        return self.documents[0]

    @property
    def primary_contact(
        self,
    ) -> Optional[
        PatientContact
    ]:
        for contact in self.contacts:
            if contact.primary:
                return contact

        if self.contacts:
            return self.contacts[0]

        return None