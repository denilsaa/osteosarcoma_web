import math

from clinica.application.dto import (
    ClinicalCaseFiltersDTO,
)

from clinica.domain.repositories import (
    ClinicalCaseRepository,
)


class ListClinicalCasesUseCase:

    def __init__(
        self,
        case_repository:
            ClinicalCaseRepository,
    ):

        self.case_repository = (
            case_repository
        )


    def execute(
        self,
        filters:
            ClinicalCaseFiltersDTO,
    ) -> dict:

        page = max(
            1,
            filters.page,
        )


        page_size = min(
            max(
                1,
                filters.page_size,
            ),
            100,
        )


        cases, total = (
            self
            .case_repository
            .list_cases(
                search=
                    filters.search,

                status_code=
                    filters.status_code,

                priority_code=
                    filters.priority_code,

                patient_id=
                    filters.patient_id,

                responsible_oncologist_uuid=
                    filters
                    .responsible_oncologist_uuid,

                opening_date=
                    filters.opening_date,

                page=
                    page,

                page_size=
                    page_size,
            )
        )


        total_pages = (
            math.ceil(
                total
                /
                page_size
            )
            if total
            else 0
        )


        return {
            "cases":
                cases,

            "pagination": {
                "page":
                    page,

                "page_size":
                    page_size,

                "total":
                    total,

                "total_pages":
                    total_pages,
            },
        }