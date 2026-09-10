from clinica.domain.repositories import (
    ClinicalCaseRepository,
)


class GetClinicalCaseCatalogsUseCase:

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
    ) -> dict:

        return (
            self
            .case_repository
            .list_catalogs()
        )