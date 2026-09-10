from uuid import UUID

from clinica.domain.repositories import (
    ClinicalCaseRepository,
)


class GetClinicalCaseUseCase:

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
        case_id:
            UUID,
    ):

        case = (
            self
            .case_repository
            .get_by_id(
                case_id,
            )
        )


        if case is None:

            raise ValueError(
                "El caso clínico no existe."
            )


        return case