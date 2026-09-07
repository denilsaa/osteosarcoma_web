from clinica.application.dto import (
    PossibleDuplicateDTO,
)
from clinica.domain.repositories import (
    PatientRepository,
)
from clinica.domain.services import (
    PatientDomainService,
)


class FindPatientDuplicatesUseCase:
    def __init__(
        self,
        repository: PatientRepository,
    ):
        self.repository = repository

    def execute(
        self,
        dto: PossibleDuplicateDTO,
    ):
        document_number = None

        if dto.document_number:
            document_number = (
                PatientDomainService
                .normalize_document(
                    dto.document_number
                )
            )

        first_names = (
            PatientDomainService
            .normalize_text(
                dto.first_names
            )
        )

        paternal_surname = (
            PatientDomainService
            .normalize_text(
                dto.paternal_surname
            )
        )

        maternal_surname = (
            PatientDomainService
            .normalize_text(
                dto.maternal_surname
            )
        )

        return (
            self.repository
            .find_possible_duplicates(
                document_type_id=
                    dto.document_type_id,

                document_number=
                    document_number,

                first_names=
                    first_names,

                paternal_surname=
                    paternal_surname,

                maternal_surname=
                    maternal_surname,

                birth_date=
                    dto.birth_date,

                limit=10,
            )
        )