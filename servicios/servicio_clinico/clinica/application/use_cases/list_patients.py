from math import ceil

from clinica.application.dto import (
    PatientFiltersDTO,
)
from clinica.domain.repositories import (
    PatientRepository,
)
from clinica.domain.services import (
    PatientDomainService,
)


class ListPatientsUseCase:
    def __init__(
        self,
        repository: PatientRepository,
    ):
        self.repository = repository

    def execute(
        self,
        dto: PatientFiltersDTO,
    ):
        page = max(
            dto.page,
            1,
        )

        page_size = min(
            max(
                dto.page_size,
                1,
            ),
            100,
        )

        search = (
            PatientDomainService
            .normalize_text(
                dto.search
            )
        )

        patients, total = (
            self.repository
            .list_patients(
                search=
                    search,

                sex_code=
                    dto.sex_code,

                active=
                    dto.active,

                document_type_code=
                    dto
                    .document_type_code,

                page=
                    page,

                page_size=
                    page_size,
            )
        )

        total_pages = (
            ceil(
                total / page_size
            )
            if total > 0
            else 1
        )

        return {
            "patients":
                patients,

            "total":
                total,

            "page":
                page,

            "page_size":
                page_size,

            "total_pages":
                total_pages,
        }