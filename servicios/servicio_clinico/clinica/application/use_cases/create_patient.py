from clinica.application.dto import (
    CreatePatientDTO,
)
from clinica.domain.exceptions import (
    DuplicatePatientError,
)
from clinica.domain.repositories import (
    PatientRepository,
)
from clinica.domain.services import (
    PatientDomainService,
)


class CreatePatientUseCase:
    def __init__(
        self,
        repository: PatientRepository,
    ):
        self.repository = repository

    def execute(
        self,
        dto: CreatePatientDTO,
    ):
        first_names = (
            PatientDomainService
            .validate_name(
                dto.first_names,
                "Los nombres",
            )
        )

        paternal_surname = (
            PatientDomainService
            .validate_name(
                dto.paternal_surname,
                "El apellido paterno",
            )
        )

        maternal_surname = (
            PatientDomainService
            .normalize_text(
                dto.maternal_surname
            )
        )

        PatientDomainService.validate_birth_date(
            dto.birth_date
        )

        document_number = (
            PatientDomainService
            .normalize_document(
                dto.document_number
            )
        )

        exact_duplicate = (
            self.repository
            .find_exact_document(
                document_type_id=
                    dto.document_type_id,
                document_number=
                    document_number,
            )
        )

        if exact_duplicate:
            raise DuplicatePatientError()

        contact_value = (
            PatientDomainService
            .normalize_contact(
                dto.contact_value
            )
        )

        return self.repository.create(
            first_names=
                first_names,

            paternal_surname=
                paternal_surname,

            maternal_surname=
                maternal_surname,

            birth_date=
                dto.birth_date,

            sex_id=
                dto.sex_id,

            document_type_id=
                dto.document_type_id,

            document_number=
                document_number,

            complement=
                PatientDomainService
                .normalize_text(
                    dto.complement
                ),

            issued_in=
                PatientDomainService
                .normalize_text(
                    dto.issued_in
                ),

            contact_type_id=
                dto.contact_type_id,

            contact_value=
                contact_value,
        )