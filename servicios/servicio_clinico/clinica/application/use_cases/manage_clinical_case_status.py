from uuid import (
    UUID,
)

from clinica.application.dto import (
    AdvanceClinicalCaseStatusDTO,
)

from clinica.domain.entities import (
    ClinicalCase,
)

from clinica.domain.repositories import (
    ClinicalCaseStatusRepository,
)


class AdvanceClinicalCaseStatusUseCase:

    def __init__(
        self,
        case_repository:
            ClinicalCaseStatusRepository,
    ):

        self.case_repository = (
            case_repository
        )


    def execute(
        self,
        dto:
            AdvanceClinicalCaseStatusDTO,
        *,
        actor_uuid:
            UUID,
    ) -> ClinicalCase:

        observation = (
            dto.observation.strip()
            if dto.observation
            else None
        )


        return (
            self.case_repository
            .advance_status(
                case_id=
                    dto.case_id,

                user_uuid=
                    actor_uuid,

                observation=
                    observation,
            )
        )


class GetClinicalCaseStatusHistoryUseCase:

    def __init__(
        self,
        case_repository:
            ClinicalCaseStatusRepository,
    ):

        self.case_repository = (
            case_repository
        )


    def execute(
        self,
        case_id:
            UUID,
    ) -> list[dict]:

        return (
            self.case_repository
            .list_status_history(
                case_id
            )
        )